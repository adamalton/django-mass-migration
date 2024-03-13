"""
Utilities for allowing you to prevent particular code functions from being run unless specific
migrations have been applied.
"""

# Standard library
from functools import wraps
import logging

# Third party
from django.http import HttpResponse

# Djangae Migrations
from .exceptions import DbAliasNotAllowed, RequiredMigrationNotApplied
from .loader import store
from .models import MigrationRecord
from .utils.test import in_tests

logger = logging.getLogger(__name__)

APPLIED_MIGRATIONS_CACHE = {}


def get_migration_key(migration_id_str_or_tuple):
    """
    Get the migration key from the provided migration ID string or tuple.

    Args:
        migration_id_str_or_tuple (str or tuple): The migration ID string or tuple.

    Returns:
        str: The migration key.

    Raises:
        ValueError: If the provided migration key doesn't exists.
    """
    if isinstance(migration_id_str_or_tuple, (list, tuple)):
        key = MigrationRecord.key_from_name_tuple(migration_id_str_or_tuple)
    else:
        key = migration_id_str_or_tuple

    if key not in store.by_key:
        raise ValueError(
            f"Provided migration with key '{key}' not found."
            f"Available keys are {', '.join(store.by_key.keys())}"
        )

    return key


def migration_is_applied(migration_identifier, db_alias):
    """ Tells you whether or not the specified migration has been applied to the DB.
        Positive (True) responses are cached to avoid repeated DB queries.
    """
    migration_key = get_migration_key(migration_identifier)
    cache_key = (get_migration_key(migration_identifier), db_alias)
    try:
        return APPLIED_MIGRATIONS_CACHE[cache_key]
    except KeyError:
        applied = MigrationRecord.objects.using(db_alias).filter(key=migration_key, is_applied=True).exists()
        if applied:
            APPLIED_MIGRATIONS_CACHE[cache_key] = True
            return True
    return False


def requires_migration(migration_identifier, db_aliases=[], is_view=False, skip_in_tests=True):
    """ Function decorator which prevents the function being run if the specified migration is not
        applied.
    """

    def decorator(function):
        @wraps(function)
        def replacement(*args, **kwargs):
            def enforce_migration():
                key = get_migration_key(migration_identifier)

                migration = store.by_key[key]

                allowed_db_aliases = migration.get_allowed_db_aliases()

                # By default if db_alias is not specified, we assume the migration needs to be applied on all the allowed_db_aliases
                # specified in the migration
                if not db_aliases:
                    required_migrations_db_aliases = allowed_db_aliases
                else:
                    if any([db_alias not in allowed_db_aliases for db_alias in db_aliases]):
                        raise DbAliasNotAllowed(
                            f"requires_migration decorator improperly configured. "
                            f"It requires the migration <{migration_identifier}> to have run on <{', '.join(db_aliases)}> "
                            f"while the allowed databases are <{', '.join(allowed_db_aliases)}>."
                        )
                    else:
                        required_migrations_db_aliases = db_aliases

                if not (skip_in_tests and in_tests()):
                    if not all([migration_is_applied(migration_identifier, db_alias) for db_alias in required_migrations_db_aliases]):
                        raise RequiredMigrationNotApplied(
                            f"Migration '{function}'' requires migration {migration_identifier} which has "
                            "not been applied."
                        )

            if is_view:
                try:
                    enforce_migration()
                except RequiredMigrationNotApplied:
                    logger.error(
                        "View function '%s' requires migration '%s' which has not yet been applied.",
                        function, migration_identifier
                    )
                    return HttpResponse(
                        "This resource requires data changes which have not yet been made.",
                        status=503,
                    )
            else:
                enforce_migration()

            return function(*args, **kwargs)
        return replacement
    return decorator


def view_requires_migration(migration_identifier, db_aliases=[], skip_in_tests=True):
    """ Same as `requires_migration`, but for view functions. Returns a 503 status HttpResponse
        rather than raising an exception.
    """
    return requires_migration(migration_identifier, is_view=True, db_aliases=db_aliases, skip_in_tests=skip_in_tests)