# Standard library
import uuid

# Third party
from django.db import models
from django.utils import timezone
from gcloudc.db.models.fields.computed import ComputedBooleanField, ComputedCharField

# Djangae Migrations
from .fields import ComputedDateTimeField
from .utils.apps import get_app_label_choices
from .utils.functional import MemoizedLazyList


class MigrationRecord(models.Model):
    """ Stores a record of a particular migration being applied to the database. """

    key = ComputedCharField("_key", primary_key=True)
    app_label = models.CharField(choices=MemoizedLazyList(get_app_label_choices))
    name = models.CharField()
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
    applied_at = ComputedDateTimeField("_applied_at")
    has_error = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)
    was_faked = models.BooleanField(default=False)

    def _key(self):
        return self.key_from_name_tuple((self.app_label, self.name))

    def _applied_at(self):
        if self.is_applied and not self.applied_at:
            return timezone.now()
        return self.applied_at

    def _in_progress(self):
        return self.initiated_at and not self.applied_at

    @staticmethod
    def key_from_name_tuple(name_tuple):
        """ Given a 2-part migration identifier, return the single string object which we use as
            the `key` field value.
        """
        assert len(name_tuple) == 2
        return ":".join(name_tuple)
