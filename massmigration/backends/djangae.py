# Standard library
import logging

# Third party
from djangae.processing import (
    datastore_key_ranges,
    firestore_name_key_ranges,
    sequential_int_key_ranges,
    uuid_key_ranges,
)
from djangae.tasks.deferred import defer, defer_iteration_with_finalize
from django.conf import settings
from django.db import models, router
try:
    from gcloudc.db.models.fields.firestore import AutoCharField
except ImportError:
    # This currently only exists in the Firestore branch of gcloudc
    AutoCharField = type("AutoCharField", (), {})

# Massmigration
from massmigration.utils.transaction import get_transaction
from .base import BackendBase

logger = logging.getLogger(__name__)


class DjangaeBackend(BackendBase):
    """ Backend for running operations on Google Cloud Tasks in Djangae projects.
        Works with SQL, Cloud Datastore and Firestore.
    """

    def run_simple(self, migration):
        defer(migration.wrapped_operation, _queue=self._get_queue_name(migration))
        logger.info("Deferred task to run single-task migration %s", migration.key)

    def run_mapper(self, migration):
        # Use `defer_iteration_with_finalize` to do the processing with whichever key_ranges_getter
        # is appropriate for the DB.
        queryset = migration.get_queryset()
        key_ranges_getter = self._key_ranges_getter(queryset)
        with get_transaction().atomic():
            attempt_uuid = migration.mark_as_started()
            defer_iteration_with_finalize(
                queryset,
                self._call_mapper_wrapped_operation,
                self._mark_mapper_as_finished,
                key_ranges_getter=key_ranges_getter,
                migration=migration,
                attempt_uuid=attempt_uuid,
                _queue=self._get_queue_name(migration),
                _transactional=True,
            )
            logger.info("Deferred task to run mapper migration %s", migration.key)

    def _get_queue_name(self, migration):
        """ Get the queue name from settings, or the override on the migration, if set."""
        queue = getattr(migration, "queue_name", None)
        if not queue:
            queue = getattr(settings, "MASSMIGRATION_TASK_QUEUE", None)
        if not queue:
            raise NotImplementedError("Please configure settings.MASSMIGRATION_TASK_QUEUE.")
        return queue

    def _call_mapper_wrapped_operation(self, instance, migration, attempt_uuid):
        migration.wrapped_operation(instance, attempt_uuid)

    def _mark_mapper_as_finished(self, migration, attempt_uuid):
        logger.info("Marking migration %s (attempt %s) as finished.", migration.key, attempt_uuid)
        migration.mark_as_finished()

    def _key_ranges_getter(self, queryset):
        # TODO: this could be better at handling the different cases
        connection = router.db_for_write(queryset.model)
        engine = settings.DATABASES[connection]["ENGINE"]
        pk_field = queryset.model._meta.pk
        if isinstance(pk_field, models.UUIDField):
            return uuid_key_ranges
        elif engine == "gcloudc.db.backends.datastore":
            return datastore_key_ranges
        elif engine == "gcloudc.db.backends.firestore":
            if isinstance(pk_field, AutoCharField):
                return firestore_name_key_ranges
        else:  # SQL
            if isinstance(pk_field, models.IntegerField):
                return sequential_int_key_ranges
        # There's also `firestore_scattered_int_key_ranges` which we might want to use in some cases
        raise NotImplementedError(
            f"Key ranges getter function for PKs of type {type(pk_field)} on DB engine '{engine}' "
            "is not yet specified."
        )
