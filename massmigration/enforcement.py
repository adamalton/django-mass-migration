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
from .exceptions import RequiredMigrationNotApplied
from .loader import is_valid_migration_id
from .models import MigrationRecord
from .utils.test import in_tests

logger = logging.getLogger(__name__)

APPLIED_MIGRATIONS_CACHE = {}


def migration_is_applied(migration_identifier):
    """ Tells you whether or not the specified migration has been applied to the DB.
        Positive (True) responses are cached to avoid repeated DB queries.
    """
    if is_valid_migration_id(migration_identifier):
        key = migration_identifier
    else:
        key = MigrationRecord.key_from_name_tuple(migration_identifier)
    try:
        return APPLIED_MIGRATIONS_CACHE[key]
    except KeyError:
        applied = MigrationRecord.objects.filter(key=key, is_applied=True).exists()
        if applied:
            APPLIED_MIGRATIONS_CACHE[key] = True
            return True
    return False


def requires_migration(migration_identifier, skip_in_tests=True):
    """ Function decorator which prevents the function being run if the specified migration is not
        applied.
    """
    def decorator(function):
        @wraps(function)
        def replacement(*args, **kwargs):
            if not (skip_in_tests or in_tests()):
                if not migration_is_applied(migration_identifier):
                    raise RequiredMigrationNotApplied(
                        f"Function '{function}'' requires migration {migration_identifier} which has "
                        "not been applied."
                    )
            return function(*args, **kwargs)
        return replacement
    return decorator


def view_requires_migration(migration_identifier, skip_in_tests=True):
    """ Same as `requires_migration`, but for view functions. Returns a 503 status HttpResponse
        rather than raising an exception.
    """
    def decorator(function):
        @wraps(function)
        def replacement(*args, **kwargs):
            if not (skip_in_tests or in_tests()):
                if not migration_is_applied(migration_identifier):
                    logger.error(
                        "View function '%s' requires migration '%s' which has not yet been applied.",
                        function, migration_identifier
                    )
                    return HttpResponse(
                        "This resource requires data changes which have not yet been made.",
                        status=503,
                    )
            return function(*args, **kwargs)
        return replacement
    return decorator
