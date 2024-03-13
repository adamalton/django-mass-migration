# Standard library
import uuid

# Third party
from django.db import models
from django.utils import timezone
from gcloudc.db.models.fields.computed import ComputedBooleanField

# Djangae Migrations
from .fields import ComputedCharField, ComputedDateTimeField
from .utils.apps import get_app_label_choices
from .utils.functional import MemoizedLazyList


class MigrationRecord(models.Model):
    """ Stores a record of a particular migration being applied to the database.
    The assumption is these models are stored on the same DB the migration has been applied to.
    """

    class Status(models.TextField):
        APPLIED = "APPLIED"
        ERRORED = "ERRORED"
        RUNNING = "RUNNING"
        NOT_RUN = "NOT_RUN"  # Can't be returned by this object, as this object won't exist

    # I'm still not sure whether the key should be computed from the app_label and name or the
    # other way round. The app_label at least is good for filtering in the Django admin though.
    key = models.CharField(max_length=250, primary_key=True)
    app_label = ComputedCharField(
        "_app_label", max_length=100, choices=MemoizedLazyList(get_app_label_choices)
    )
    name = ComputedCharField("_name", max_length=150)
    attempt_uuid = models.UUIDField(
        default=uuid.uuid4,
        help_text=(
            "A unique ID which allows us to detect if this object was deleted and recreated (e.g. "
            "due to an error), and therefore allows us to abort any stale tasks which were spawned "
            "as part of the previous attempt of the same migration."
        ),
        editable=False,
    )
    # We don't have an `is_initiated` field, as if it's not initiated it won't exist in the DB.
    initiated_at = models.DateTimeField(default=timezone.now, editable=False)
    in_progress = ComputedBooleanField("_in_progress")
    is_applied = models.BooleanField(
        default=False, help_text="Is the migration fully applied to the DB?"
    )
    applied_at = ComputedDateTimeField("_applied_at", null=True)
    has_error = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)
    was_faked = models.BooleanField(default=False)

    def _app_label(self):
        return self.key.split(":")[0]

    def _name(self):
        return self.key.split(":")[1]

    def _applied_at(self):
        if self.is_applied and not self.applied_at:
            return timezone.now()
        return self.applied_at

    def _in_progress(self):
        return not (self.is_applied or self.has_error)

    @staticmethod
    def key_from_name_tuple(name_tuple):
        """ Given a 2-part migration identifier, return the single string object which we use as
            the `key` field value.
        """
        assert len(name_tuple) == 2
        return ":".join(name_tuple)

    def status(self):
        if self.has_error:
            return self.Status.ERRORED
        if self.is_applied:
            return self.Status.APPLIED
        return self.Status.RUNNING
