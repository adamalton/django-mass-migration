from massmigration.migrations import SimpleMigration


class Migration(SimpleMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    # This can be set to specify the list of database aliases on which the migration can be applied.
    # The migration is not forced on a specific DB but rather the `db_alias` for the DB is passed to `operation`
    # allowing to customise what is retrieved by the migration.
    # If None the migration can be applied to all databases.
    allowed_db_aliases: list = None

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def operation(self, db_alias):

        # PUT YOUR CODE HERE.
        # It should perform the entire migration operation in this single step.
        # This must be complete-able within the memory and time limits of the backend.
        # If you cannot perform the operation within a single operation, then you should use the
        # 'mapper' or 'custom' template instead.

        raise NotImplementedError
