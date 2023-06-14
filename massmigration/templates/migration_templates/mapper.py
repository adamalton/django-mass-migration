from massmigration.migrations import MapperMigration


class Migration(MapperMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def get_queryset(self):
        raise NotImplementedError(
            "Replace this with your code. It must return a queryset for the objects which you wish "
            "to perform the operation on."
        )

    def operation(self, obj):
        raise NotImplementedError(
            "Replace this with your code. It should perform the operation on the given object, "
            "which will be an instance from the queryset."
        )
