# Third party
from django.contrib import admin
from django.contrib.admin.templatetags.admin_list import _boolean_icon

# Mass Migration
from .loader import store
from .models import MigrationRecord


class MigrationRecordAdmin(admin.ModelAdmin):
    """ Custom admin class for the Migration model. """

    ordering = ("-initiated_at",)
    list_display = ("key", "initiated_at", "is_applied", "successful", "applied_at", "was_faked")
    list_filter = ("app_label", "is_applied", "was_faked")
    readonly_fields = ("app_label", "name", "description")

    def description(self, obj):
        migration = store.by_key[obj.key]
        return migration.description

    def successful(self, obj):
        return _boolean_icon((not obj.has_error) if obj.is_applied else None)


admin.site.register(MigrationRecord, MigrationRecordAdmin)
