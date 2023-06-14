# Third party
from django.contrib import admin

# Djangae Migrations
from .models import MigrationRecord


class AppLabelFilter():
    # TODO: make a filter for the `MigrationRecord.app_label` field, but rather than getting the
    # possible values from the DB, provide them as choices from django.apps.get_apps() or whatever
    # that thing is. Although maybe that's not necessary? Can we just set `choices` on the
    # Migration.app_label field?
    pass


class MigrationRecordAdmin(admin.ModelAdmin):
    """ Custom admin class for the Migration model. """

    ordering = ("-initiated_at",)
    list_display = ("name", "initiated_at", "is_applied", "applied_at")


admin.site.register(MigrationRecord, MigrationRecordAdmin)
