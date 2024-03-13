""" A set of utility functions to aid programmatic control of migrations.
    These are really just a collation of functionality from around the app.
"""

# Standard library
from typing import List

# Mass Migration
from . import enforcement
from .exceptions import MigrationAlreadyStarted
from .loader import store
from .migrations import BaseMigration
from .models import MigrationRecord


def get_all_migrations() -> List[BaseMigration]:
    """ Returns a list of all migrations from all installed apps, ordered by app. """
    return store.all


def migration_is_applied(migration: BaseMigration, db_alias: str) -> bool:
    """ Is the given migration applied? """
    return enforcement.migration_is_applied(migration.key, db_alias)


def migration_was_started(migration: BaseMigration, db_alias: str) -> bool:
    """ Has the given migration ever been initiated (even if it hasn't finished or it failed)? """
    return MigrationRecord.objects.using(db_alias).filter(key=migration.key).exists()


def migration_is_in_progress(migration: BaseMigration, db_alias: str) -> bool:
    """ Is the given migration currently running (started but not yet finished and not errored)? """
    return MigrationRecord.objects.using(db_alias).filter(
        key=migration.key, is_applied=False, has_error=False
    ).exists()


def can_start_migration(migration: BaseMigration, db_alias: str) -> bool:
    """ Can the given migration be started? I.e. either it's never been started or all previous
        attempts have errored.
    """
    return not MigrationRecord.objects.using(db_alias).filter(key=migration.key).exclude(
        has_error=True
    ).exists()


def initiate_migration(migration: BaseMigration, db_alias: str) -> bool:
    if migration_is_in_progress(migration):
        raise MigrationAlreadyStarted(f"Migration {migration.key} on db '{db_alias}' is already running.")
    migration.launch(db_alias)
