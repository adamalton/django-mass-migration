# Standard library
import logging

# Third party
from djangae.tasks.deferred import defer, defer_iteration_with_finalize
from django.conf import settings

# Massmigration
from massmigration.utils.transaction import get_transaction
from .base import BackendBase

logger = logging.getLogger(__name__)


class DjangaeBackend(BackendBase):
    """ Djangae-based backend for running operations on Google Cloud Tasks. """

    def run_simple(self, migration):
        defer(migration.wrapped_operation, _queue=self._get_queue_name(migration))
        logger.info("Deferred task to run single-task migration %s", migration.key)

    def run_mapper(self, migration):
        with get_transaction().atomic():
            attempt_uuid = migration.mark_as_started()
            defer_iteration_with_finalize(
                migration.get_queryset(),
                self._call_mapper_wrapped_operation,
                self._mark_mapper_as_finished,
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
        migration.mark_as_finished()
