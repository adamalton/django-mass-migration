# Standard library
import threading

# Djangae migrations
from .models import MigrationRecord


cache = threading.local()


def get_migration(key):
    """ Return the MigrationRecord for the given key. This is done with a local per-request cache
        (which for the MapperMigration means a per-task cache) to avoid excessive DB hits. So the
        returned migration may be out of date, but will be refreshed for each new request.
    """
    _ensure_cache()
    try:
        migration = cache.migrations[key]
    except KeyError:
        # If the migration doesn't exist we still cache that to avoid repeated DB calls
        migration = MigrationRecord.objects.filter(key=key).first()
        cache.migrations[key] = migration
    return migration


def remove_migration(key):
    """ Remove the migration of the given key from the current request's cache. This is useful when
        a migration has been updated in the DB (e.g. because of an error) and you want subsequent
        checks to get the new version from the DB.
    """
    _ensure_cache()
    try:
        del cache.migrations[key]
    except KeyError:
        pass


def _ensure_cache():
    if not hasattr(cache, "migrations"):
        cache.migrations = {}
