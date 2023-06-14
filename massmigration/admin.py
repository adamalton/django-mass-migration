# Third party
from django.contrib import admin

# Mass Migration
from .loader import store
from .models import MigrationRecord


class MigrationRecordAdmin(admin.ModelAdmin):
    """ Custom admin class for the Migration model. """

    ordering = ("-initiated_at",)
    list_display = ("key", "initiated_at", "is_applied", "applied_at", "was_faked")
    list_filter = ("app_label", "is_applied", "was_faked")
    readonly_fields = ("app_label", "name", "description")

    def description(self, obj):
        migration = store.by_key[obj.key]
        return migration.description


admin.site.register(MigrationRecord, MigrationRecordAdmin)
