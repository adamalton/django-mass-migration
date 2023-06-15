from massmigration.migrations import BaseMigration


class Migration(BaseMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    # For a custom migration, you must set this, and your backend must have this method.
    backend_method: str = NotImplemented

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def launch(self):
        self.check_dependencies()
        self.mark_as_started()

        # PUT YOUR CODE HERE.
        # It should defer whatever operation(s) you want to perform to a backend which knows how to
        # perform them.
        # When done, or when an error occurs, the backend must call mark_as_finished() or
        # mark_as_errored_() on this object as appropriate.

        raise NotImplementedError
