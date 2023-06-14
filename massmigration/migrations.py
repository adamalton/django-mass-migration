# Standard library
import logging

# Third party
from gcloudc.db import transaction
from djangae.tasks.deferred import defer, defer_iteration_with_finalize
from djangae.utils import retry_on_error
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

# Djangae Migrations
from . import loader
from . import per_request_cache
from .exceptions import DependentMigrationNotApplied, MigrationAlreadyStarted
from .models import MigrationRecord


logger = logging.getLogger(__name__)


class BaseMigration:
    """ An operation to be performed on the database. """

    dependencies = []  # A list of (app_label, migration_name) pairs

    # Which task queue to use when running tasks to apply the migration. Defaults to
    # settings.MIGRATIONS_TASK_QUEUE_NAME
    queue = None

    # Use this only if you're not storing your migrations in a folder called 'migrations'
    app_label = None

    @cached_property
    def key_tuple(self):
        """ Returns the (app_label, file_name) tuple of this migration based on the file name.
            This should uniquely identify this migration in the project.
        """
        return loader.get_key_tuple(self.__class__)

    @property
    def key(self):
        """ A string which uniquely identifies this migration in the system. """
        return ":".join(self.key_tuple)

    @property
    def _queue_name(self):
        if self.queue:
            return self.queue
        queue = getattr(settings, "MIGRATIONS_TASK_QUEUE_NAME", None)
        if not queue:
            raise NotImplementedError("Please configure settings.MIGRATIONS_TASK_QUEUE_NAME.")
        return queue

    def start(self):
        """ Defer the background task(s) to perform the operation on the database.
            This is what should be called by the web interface to trigger the migration.
        """
        # I think this should probably be left unimplemented so that the subclasses implement their
        # specific needs for it
        raise NotImplementedError

    def mark_as_started(self):
        """ Mark the migration as started in the database. """
        with transaction.atomic():
            migration = MigrationRecord.objects.get(key=self.key)
            if migration.initiated_at:
                raise MigrationAlreadyStarted(
                    f"Migration {self.__class__.__name__} has already been initiated."
                )
            migration.initiated_at = timezone.now()
            migration.save()

    @retry_on_error()
    def mark_as_errored(self, error=None):
        """ Mark the migration as errored in the database. """
        per_request_cache.remove_migration(self.key)
        # TODO: Generate a proper traceback here
        error_str = f"{error.__class__.__name__}: {error}"
        MigrationRecord.objects.filter(key=self.key).update(has_error=True, last_error=error_str)

    @retry_on_error()
    def mark_as_finished(self):
        """ Mark the migration as applied/finalized in the database. """
        with transaction.atomic():
            migration = MigrationRecord.objects.get(key=self.key)
            if migration.is_applied:
                logger.warning("Migration %s is already marked as applied.", self.key)
            else:
                migration.is_applied = True
                migration.save()
                logger.info("Migration %s finished. Marked it as applied.", self.key)

    def check_dependencies(self):
        """ Make sure that any migrations which this migration depends on have been applied. """
        # TODO: check that the specified migrations actually exist in the code.
        dependency_keys = [MigrationRecord.key_from_name_tuple(x) for x in self.dependencies]
        applied_keys = MigrationRecord.objects.filter(
            is_applied=True, key__in=dependency_keys
        ).values_list("pk", flat=True)
        for dependency_key in dependency_keys:
            if dependency_key not in applied_keys:
                raise DependentMigrationNotApplied(
                    f"Migration {self.key} depends on migration {dependency_key}, which has not "
                    "yet been applied."
                )


class SimpleMigration(BaseMigration):
    """ A migration which only needs to apply a very quick and simple change to the database which
        can be applied by one call of one function which can run in the time and memory constraints
        of one task.
    """

    def operation(self):
        raise NotImplementedError("The `operation` method must be implemented by subclasses.")

    def start(self):
        self.check_dependencies()
        self.mark_as_started()
        defer(self._run, _queue=self._queue_name)
        logger.info("Deferred task to run single-task migration %s", self.key)

    def _run(self):
        try:
            self.operation()
        except Exception as error:
            self.mark_as_errored(error)
        else:
            self.mark_as_finished()


class MapperMigration(BaseMigration):
    """ A migration which calls a function on each object in a queryset. """

    def get_queryset(self):
        """ Returns the Django queryset which is to be mapped over. """
        raise NotImplementedError("The `get_queryset` method must be implemented by subclasses.")

    def operation(self, obj: models.Model) -> None:
        """ This is what will get called on each model instance in the queryset. """
        raise NotImplementedError("The `operation` method must be implemented by subclasses.")

    def start(self):
        self.check_dependencies()
        self.mark_as_started()
        migration = MigrationRecord.objects.get(key=self.key)
        defer_iteration_with_finalize(
            self.get_queryset(),
            self._wrapped_operation,
            self.mark_as_finished,
            attempt_uuid=migration.attempt_uuid,
            _queue=self._queue_name,
        )
        logger.info("Deferred task to run mapper migration %s", self.key)

    def _wrapped_operation(self, obj, attempt_uuid):
        """ Call self.operation() on the object, but wrap it to catch any errors and set the
            migration as failed.
        """
        key = self.key
        migration = per_request_cache.get_migration(key)
        if migration is None:
            logger.warning(
                "Migration %s no longer exists in the DB. Skipping processing operation.", key
            )
        elif migration.attempt_uuid != attempt_uuid:
            logger.warning(
                "Migration %s now has attempt %s. Skipping processing operation from attempt %s.",
                key, migration.attempt_uuid, attempt_uuid
            )
        elif migration.has_error:
            logger.warning(
                "Migration %s is marked in the DB as having errors. Skipping processing operation.",
                key,
            )
        else:
            # We could log the object with just str(obj) here, but as the model might have a custom
            # __str__ method which does DB lookups, we just use the PK to ensure efficiency
            logger.info(
                "Running operation for migration %s on %s (pk=%r).",
                key,
                obj.__class__.__name__,
                obj.pk,
            )
            try:
                self.operation(obj)
            except Excetion as error:
                logger.exception(
                    "Error in migration %s trying to process object %s (pk=%r).",
                    key,
                    obj.__class__.__name__,
                    obj.pk,
                )
                self.mark_as_errored(error)
