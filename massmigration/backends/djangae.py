# Standard library
import logging
import warnings

# Third party
from djangae.processing import (
    datastore_key_ranges,
    firestore_name_key_ranges,
    firestore_scattered_int_key_ranges,
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

        Optional `backend_params`:
        - `defer_kwargs` - these get passed through to `defer` for simple migrations.
        - `defer_iteration_with_finalize_kwargs` - these get passed through to
            `defer_iteration_with_finalize` for mapper migrations.
    """

    def run_simple(self, migration, db_alias):
        defer_kwargs = {
            "_queue": self._get_queue_name(migration),
            "_using": db_alias,
            **migration.get_backend_params().get("defer_kwargs", {}),
        }
        defer(migration.wrapped_operation, db_alias, **defer_kwargs)
        logger.info("Deferred task to run single-task migration %s", migration.key)

    def run_mapper(self, migration, db_alias):
        # Use `defer_iteration_with_finalize` to do the processing with whichever key_ranges_getter
        # is appropriate for the DB.
        queryset = migration.get_queryset(db_alias)
        key_ranges_getter = self._key_ranges_getter(queryset)
        params = migration.get_backend_params()
        # Legacy backwards compatibility
        if "key_ranges_getter" in params:
            warnings.warn(
                "Use of backend_params['key_ranges_getter'] is deprecated. "
                "Use backend_params['defer_iteration_with_finalize_kwargs']['key_ranges_getter'] ",
                "instead."
            )
            key_ranges_getter = params["key_ranges_getter"]
        # End backwards compatibility
        defer_iteration_with_finalize_kwargs = {
            "key_ranges_getter": key_ranges_getter,
            "migration": migration,
            "db_alias": db_alias,
            "_queue": self._get_queue_name(migration),
            "_transactional": True,
            **params.get("defer_iteration_with_finalize_kwargs", {}),
        }
        with get_transaction(db_alias).atomic(using=db_alias):
            attempt_uuid = migration.mark_as_started(db_alias)
            defer_iteration_with_finalize(
                queryset,
                self._call_mapper_wrapped_operation,
                self._mark_mapper_as_finished,
                attempt_uuid=attempt_uuid,
                **defer_iteration_with_finalize_kwargs,
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

    def _call_mapper_wrapped_operation(self, instance, migration, attempt_uuid, db_alias):
        migration.wrapped_operation(instance, attempt_uuid, db_alias)

    def _mark_mapper_as_finished(self, migration, attempt_uuid, db_alias):
        logger.info("Marking migration %s (attempt %s) as finished.", migration.key, attempt_uuid)
        migration.mark_as_finished(db_alias)

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
            elif isinstance(pk_field, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
                return firestore_scattered_int_key_ranges
        else:  # SQL
            if isinstance(pk_field, models.IntegerField):
                return sequential_int_key_ranges
        # There's also `firestore_scattered_int_key_ranges` which we might want to use in some cases
        raise NotImplementedError(
            f"Key ranges getter function for PKs of type {type(pk_field)} on DB engine '{engine}' "
            "is not yet specified."
        )
