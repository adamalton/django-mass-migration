from massmigration.migrations import MapperMigration


class Migration(MapperMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    # This can be set to specify the list of database aliases on which the migration can be applied.
    # The migration is not forced on a specific DB but rather the `db_alias` for the DB is passed to `get_queryset`
    # allowing to customise what is retrieved by the migration.
    # If None the migration can be applied to all databases.
    allowed_db_aliases: list = None


    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def get_queryset(self, db_alias):

        # PUT YOUR CODE HERE.
        # It must return a queryset for the objects which you wish to perform the operation on.

        raise NotImplementedError

    def operation(self, obj, db_alias):

        # PUT YOUR CODE HERE.
        # It should perform the operation on the given object which will be an instance from the
        # queryset.

        raise NotImplementedError
