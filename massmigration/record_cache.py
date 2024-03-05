""" Utilities for getting information about MigrationRecord objects without hammering the DB too much."""

# Third party
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_save

# Mass Migration
from massmigration.models import MigrationRecord


DEFAULT_CACHE_TIMEOUT = 60


def get_record(key, db_alias):
    """ Get the MigrationRecord for the given key. This is designed to be called heavily, i.e. for
        every object in a MapperMigration, so the result is cached with a best-effort attempt to
        refresh that cache when the record changes, but with no guarantee of it.
    """
    cache_key = get_cache_key(key, db_alias)
    record = cache.get(cache_key)
    if not record:
        record = MigrationRecord.objects.filter(key=key).first()
        cache.set(cache_key, record, cache_timeout())
    return record


def get_cache_key(migration_key, db_alias):
    return f"massmigration_record:{migration_key}:{db_alias}"


def cache_timeout():
    return getattr(settings, "MASSMIGRATION_RECORD_CACHE_TIMEOUT", DEFAULT_CACHE_TIMEOUT)


def record_post_save(sender, **kwargs):
    """ Update the cache when a MigrationRecord is changed (the relevant scenarios being when it's
        marked as started, marked as errored or marked as finished).
    """
    record = kwargs["instance"]
    cache_key = get_cache_key(record.key, record._state.db)
    cache.set(cache_key, record, cache_timeout())


post_save.connect(record_post_save, sender=MigrationRecord)
