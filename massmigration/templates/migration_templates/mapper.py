from massmigration.migrations import MapperMigration


class Migration(MapperMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def get_queryset(self):

        # PUT YOUR CODE HERE.
        # It must return a queryset for the objects which you wish to perform the operation on.

        raise NotImplementedError

    def operation(self, obj):

        # PUT YOUR CODE HERE.
        # It should perform the operation on the given object which will be an instance from the
        # queryset.

        raise NotImplementedError
