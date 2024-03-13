from massmigration.migrations import BaseMigration


class Migration(BaseMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    # For a custom migration, you must set this, and your backend must have this method.
    backend_method: str = NotImplemented

    # This can be set to specify the list of database aliases on which the migration can be applied.
    # The migration is not forced on a specific DB but rather the `db_alias` for the DB is passed to `launch`
    # allowing to customise what is retrieved by the migration.
    # If None the migration can be applied to all databases.
    allowed_db_aliases: list = None

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def launch(self, db_alias):
        self.check_dependencies(db_alias)
        self.mark_as_started(db_alias)

        # PUT YOUR CODE HERE.
        # It should defer whatever operation(s) you want to perform to a backend which knows how to
        # perform them.
        # When done, or when an error occurs, the backend must call mark_as_finished(db_alias) or
        # mark_as_errored_(db_alias) on this object as appropriate.

        raise NotImplementedError
