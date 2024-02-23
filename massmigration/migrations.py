# Standard library
from functools import cached_property
from uuid import UUID
import logging

# Third party
from djangae.utils import retry_on_error
from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string
from pyparsing import OnlyOnce

# Mass Migration
from . import record_cache
from .constants import DEFAULT_BACKEND
from .exceptions import CannotRunOnGivenConnection, DependentMigrationNotApplied, InvalidDbAlias, MigrationAlreadyStarted
from .models import MigrationRecord
from .utils.transaction import get_transaction


logger = logging.getLogger(__name__)


# TODO: Not fond of the fact that we have 2 different ways to represent a "no selected db", None and this sentinel.
# For migration records, see `get_database_alias_for_migration_records` in `BaseMigration` class. we use None to represent
#  no database, because it's handy to just pass it directly to .using() calls.
# Consider killing the sentinel.
class NoSelectedDB:
    def __str__(self):
        # Calling it default here would be confusiong, since
        # default is generally the default database alias while this is the case
        # where no database is "forced" and Django does what is supposed to do.
        return "auto_selected_db"
    pass


no_selected_db_sentinel = NoSelectedDB()


def _get_valid_db_aliases():
    return list(settings.DATABASES.keys()) + [no_selected_db_sentinel]


def _is_valid_db_alias(db_alias):
    if db_alias in _get_valid_db_aliases():
        return True
    return False


class BaseMigration:
    """ An operation to be performed on the database. """

    dependencies = []  # A list of (app_label, migration_name) pairs

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # specified in the Django settings
    backend: str = None

    # This specifies the name of the method on the backend class which should be called to run this
    # migration. Custom migration types can be run on custom backends which support them by using
    # this attribute.
    backend_method: str = None

    # We always allow the migration to run without specifying a using. Letting Django (and Django router) do its course.
    # If None, the migration can be run on all the available databases.
    allowed_database_aliases = None

    migration_record_db_alias = None

    @classmethod
    def get_allowed_databases(cls):
        """
        Returns a list of allowed database aliases for running the
        migration assuming that letting Django (and Django router) do its
        course is always an allowed option.
        If `allowed_database_aliases` is None, the migration can be run on
        all databases.
        """
        available_dbs = _get_valid_db_aliases()

        if cls.allowed_database_aliases is None:  # If None we assume can run on all DBs
            if len(available_dbs) > 1:  # If we only have one DB there's no need to add it, since we alread have the no_selected_db_sentinel
                allowed_db_aliases = available_dbs
        else:
            allowed_db_aliases =  [no_selected_db_sentinel] + cls.allowed_database_aliases

        return allowed_db_aliases

    def __init__(self, app_label, name, database_alias=no_selected_db_sentinel):
        self.app_label = app_label
        self.name = name
        self.database_alias = database_alias
        if not _is_valid_db_alias(self.database_alias):
            valid_db_aliases = [str(x) for x in _get_valid_db_aliases()]
            raise InvalidDbAlias(f"The provided <database_alias> is not valid. "
                                 f"Got: <{str(self.database_alias)}>, expected valid database aliases are {', '.join(valid_db_aliases)}.")

        self._check_allowed_db_aliases()

    @cached_property
    def db_for_migration_records(self):
        return self.get_database_alias_for_migration_records(self.database_alias)

    @property
    def key(self):
        """ A string which uniquely identifies this migration in the system. """
        return f"{self.app_label}:{self.name}:{self.database_alias}"

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

    def launch(self):
        """ Pass the migration to the backend to perform the data operation(s).
            This is what should be called by the web interface to trigger the migration.
        """
        self.check_dependencies()
        self.check_can_run_on_database()
        backend = self.get_backend()
        method = getattr(backend, self.backend_method)
        method(self)
        logger.info("Launched migration %s on backend %s", self.key, backend.__class__)

    def _check_allowed_db_aliases(self):
        for db_alias in self.get_allowed_databases():
            if not _is_valid_db_alias(db_alias):
                valid_db_aliases = [str(x) for x in _get_valid_db_aliases()]
                raise InvalidDbAlias(f"Invalid allowed_database_aliases provided."
                                     f"Got: <{db_alias}> but the expected valid database aliases are {', '.join(valid_db_aliases)}.")

    def check_can_run_on_database(self) -> bool:
        """
        Checks if the migration can run on the given database.

        Args:

        Returns:
            bool: True if the migration can run on the given database, False otherwise.

        Raises:
            CannotRunOnGivenConnection: If the migration cannot run on the given database.
        """
        allowed_database_aliases = self.get_allowed_databases()

        can_run = (
            self.database_alias in allowed_database_aliases or
            self.database_alias is None
        )
        if not can_run:
            raise CannotRunOnGivenConnection(
                f"Migration {self.key} can't run on {self.database_alias}. "
                f"The available connections are {', '.join(allowed_database_aliases)}. "
            )
        return can_run

    def can_be_started(self) -> bool:
        return not MigrationRecord.objects.using(self.db_for_migration_records).filter(key=self.key).exists()

    def mark_as_started(self) -> UUID:
        """ Mark the migration as started in the database. Return the attempt UUID. """
        with get_transaction().atomic(using=self.database_alias):
            if not self.can_be_started():
                raise MigrationAlreadyStarted(
                    f"Migration {self.__class__.__name__} has already been initiated."
                )
            migration = MigrationRecord.objects.create(key=self.key)
            return migration.attempt_uuid

    @retry_on_error()
    def mark_as_errored(self, error=None):
        """ Mark the migration as errored in the database. """
        # TODO: Generate a proper traceback here
        error_str = f"{error.__class__.__name__}: {error}"
        MigrationRecord.objects.using(self.db_for_migration_records).filter(key=self.key).update(has_error=True, last_error=error_str)

    @retry_on_error()
    def mark_as_finished(self):
        """ Mark the migration as applied/finalized in the database. """
        with get_transaction().atomic(using=self.database_alias):
            migration = MigrationRecord.objects.using(self.db_for_migration_records).get(key=self.key)
            if migration.is_applied:
                logger.warning("Migration %s is already marked as applied.", self.key)
            else:
                migration.is_applied = True
                migration.save(using=self.database_alias)
                logger.info("Migration %s finished. Marked it as applied.", self.key)

    def check_dependencies(self):
        """ Make sure that any migrations which this migration depends on have been applied. """
        # TODO: check that the specified migrations actually exist in the code.
        dependency_keys = [MigrationRecord.key_from_name_tuple(x) for x in self.dependencies]
        applied_keys = MigrationRecord.objects.using(self.db_for_migration_records).filter(
            is_applied=True, key__in=dependency_keys
        ).values_list("pk", flat=True)
        for dependency_key in dependency_keys:
            if dependency_key not in applied_keys:
                raise DependentMigrationNotApplied(
                    f"Migration {self.key} depends on migration {dependency_key}, which has not "
                    "yet been applied."
                )

    def get_database_alias_for_migration_records(self, database_alias):
        """
        Returns the database alias to save migration records into.
        By default we let Django decide, but subclasses can override this to force migration records to be saved
        in a specific database.

        Parameters:
        - database_alias (str): The alias of the database.

        Returns:
        - str: The database alias for migration records.
        """

        return None


class SimpleMigration(BaseMigration):
    """ A migration which only needs to apply a very quick and simple change to the database which
        can be applied by one call of one function which can run in the time and memory constraints
        of one task.
    """

    backend_method = "run_simple"

    def operation(self):
        raise NotImplementedError("The `operation` method must be implemented by subclasses.")

    def wrapped_operation(self):
        logger.info("Running operation for migration %s", self.key)
        self.mark_as_started()
        try:
            self.operation()
        except Exception as error:
            self.mark_as_errored(error)
        else:
            self.mark_as_finished()


class MapperMigration(BaseMigration):
    """ A migration which calls a function on each object in a queryset. """

    backend_method = "run_mapper"

    def get_queryset(self):
        """ Returns the Django queryset which is to be mapped over. """
        queryset = self._get_queryset_without_namespace()
        if self.database_alias is not no_selected_db_sentinel:
            queryset = queryset.using(self.database_alias)

        return queryset

    def _get_queryset_without_namespace(self):
        """ Returns the Django queryset which is to be mapped over. """
        raise NotImplementedError("The `_get_queryset_without_namespace` method must be implemented by subclasses.")

    def operation(self, obj: models.Model) -> None:
        """ This is what will get called on each model instance in the queryset. """
        raise NotImplementedError("The `operation` method must be implemented by subclasses.")

    def wrapped_operation(self, obj, attempt_uuid):
        """ Call self.operation() on the object, but wrap it to catch any errors and set the
            migration as failed if necessary.
        """
        key = self.key
        record = record_cache.get_record(key)
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
                self.operation(obj)
            except Exception as error:
                logger.exception(
                    "Error in migration %s trying to process object %s (pk=%r).",
                    key,
                    obj.__class__.__name__,
                    obj.pk,
                )
                self.mark_as_errored(error)
