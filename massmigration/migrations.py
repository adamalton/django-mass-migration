# Standard library
from uuid import UUID
import logging

# Third party
from djangae.utils import retry_on_error
from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

# Mass Migration
from . import record_cache
from .constants import DEFAULT_BACKEND
from .exceptions import (
    CannotRunOnDB,
    DbAliasNotAllowed,
    DependentMigrationNotApplied,
    MigrationAlreadyStarted
)
from .models import MigrationRecord
from .utils.transaction import get_transaction


logger = logging.getLogger(__name__)


# TODO: Is there a better place for this?
def get_all_db_aliases():
    return list(settings.DATABASES.keys())


class BaseMigration:
    """ An operation to be performed on the database. """

    allowed_db_aliases = None

    dependencies = []  # A list of (app_label, migration_name) pairs

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # specified in the Django settings
    backend: str = None

    # This specifies the name of the method on the backend class which should be called to run this
    # migration. Custom migration types can be run on custom backends which support them by using
    # this attribute.
    backend_method: str = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        all_db_aliases = get_all_db_aliases()

        if (
            cls.allowed_db_aliases is not None and  # If not set, then all dbs are allowed
            any([allowed_db not in all_db_aliases for allowed_db in cls.allowed_db_aliases])
        ):
            raise DbAliasNotAllowed(
                    f"Migration {self.key} provided invalid value(s) in `allowed_database_aliases`. "
                    f"Got <{cls.allowed_db_aliases}> while the available dbs are {', '.join(all_db_aliases)}. "
                )

    @classmethod
    def get_allowed_db_aliases(cls):
        if cls.allowed_db_aliases is None:
            return get_all_db_aliases()
        return cls.allowed_db_aliases

    def __init__(self, app_label, name):
        self.app_label = app_label
        self.name = name

    @property
    def key(self):
        """ A string which uniquely identifies this migration in the system. """
        return f"{self.app_label}:{self.name}"

    @property
    def description(self):
        # Allows the docstring to be accessed from templates despite its double underscore name
        return self.__doc__

    @property
    def backend_str(self):
        return (
            self.backend or
            getattr(settings, "MASSMIGRATION_BACKEND", None) or
            DEFAULT_BACKEND
        )

    def get_backend(self):
        backend_class = import_string(self.backend_str)
        return backend_class()

    def launch(self, db_alias):
        """ Pass the migration to the backend to perform the data operation(s).
            This is what should be called by the web interface to trigger the migration.
        """
        allowed_db_aliases = self.get_allowed_db_aliases()
        if db_alias not in allowed_db_aliases:
            raise CannotRunOnDB(
                f"Migration {self.key} can't run on {db_alias}. "
                f"The allowed DBs for this migration are {', '.join(allowed_db_aliases)}. "
            )

        self.check_dependencies(db_alias)
        backend = self.get_backend()
        method = getattr(backend, self.backend_method)
        method(self, db_alias)
        logger.info("Launched migration %s on backend %s", self.key, backend.__class__)

    def can_be_started(self, db_alias) -> bool:
        return not MigrationRecord.objects.using(db_alias).filter(key=self.key).exists()

    def mark_as_started(self, db_alias) -> UUID:
        """ Mark the migration as started in the database. Return the attempt UUID. """
        with get_transaction(db_alias).atomic(using=db_alias):
            if not self.can_be_started(db_alias):
                raise MigrationAlreadyStarted(
                    f"Migration {self.__class__.__name__} has already been initiated."
                )
            migration = MigrationRecord.objects.using(db_alias).create(
                key=self.key,
            )
            return migration.attempt_uuid

    @retry_on_error()
    def mark_as_errored(self, db_alias, error=None):
        """ Mark the migration as errored in the database. """
        # TODO: Generate a proper traceback here
        error_str = f"{error.__class__.__name__}: {error}"
        MigrationRecord.objects.using(db_alias).filter(key=self.key).update(has_error=True, last_error=error_str)

    @retry_on_error()
    def mark_as_finished(self, db_alias):
        """ Mark the migration as applied/finalized in the database. """
        with get_transaction(db_alias).atomic(using=db_alias):
            migration = MigrationRecord.objects.using(db_alias).get(key=self.key)
            if migration.is_applied:
                logger.warning("Migration %s is already marked as applied.", self.key)
            else:
                migration.is_applied = True
                migration.save()
                logger.info("Migration %s finished. Marked it as applied.", self.key)

    def check_dependencies(self, db_alias):
        """ Make sure that any migrations which this migration depends on have been applied. """
        # TODO: check that the specified migrations actually exist in the code.
        dependency_keys = [MigrationRecord.key_from_name_tuple(x) for x in self.dependencies]
        applied_keys = MigrationRecord.objects.using(db_alias).filter(
            is_applied=True, key__in=dependency_keys
        ).values_list("pk", flat=True)
        for dependency_key in dependency_keys:
            if dependency_key not in applied_keys:
                raise DependentMigrationNotApplied(
                    f"Migration {self.key} depends on migration {dependency_key}, which has not "
                    "yet been applied."
                )

    def get_migration_record(self, db_alias):
        return MigrationRecord.objects.using(db_alias).filter(key=self.key).first()


class SimpleMigration(BaseMigration):
    """ A migration which only needs to apply a very quick and simple change to the database which
        can be applied by one call of one function which can run in the time and memory constraints
        of one task.
    """

    backend_method = "run_simple"

    def operation(self, db_alias):
        raise NotImplementedError("The `operation` method must be implemented by subclasses.")

    def wrapped_operation(self, db_alias):
        logger.info("Running operation for migration %s", self.key)
        self.mark_as_started(db_alias)
        try:
            self.operation(db_alias)
        except Exception as error:
            self.mark_as_errored(db_alias, error)
        else:
            self.mark_as_finished(db_alias)


class MapperMigration(BaseMigration):
    """ A migration which calls a function on each object in a queryset. """

    backend_method = "run_mapper"

    def get_queryset(self, db_alias):
        """ Returns the Django queryset which is to be mapped over. """
        raise NotImplementedError("The `get_queryset` method must be implemented by subclasses.")

    def operation(self, obj: models.Model, db_alias: str) -> None:
        """ This is what will get called on each model instance in the queryset. """
        raise NotImplementedError("The `operation` method must be implemented by subclasses.")

    def wrapped_operation(self, obj, attempt_uuid, db_alias):
        """ Call self.operation() on the object, but wrap it to catch any errors and set the
            migration as failed if necessary.
        """
        key = self.key
        record = record_cache.get_record(self.key, db_alias)
        if record is None:
            logger.warning(
                "Migration %s no longer exists in the DB. Skipping processing operation.", key
            )
        elif record.attempt_uuid != attempt_uuid:
            logger.warning(
                "Migration %s now has attempt %s. Skipping processing operation from attempt %s.",
                key, record.attempt_uuid, attempt_uuid
            )
        elif record.has_error:
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
                self.operation(obj, db_alias)
            except Exception as error:
                logger.exception(
                    "Error in migration %s trying to process object %s (pk=%r).",
                    key,
                    obj.__class__.__name__,
                    obj.pk,
                )
                self.mark_as_errored(error, db_alias)
