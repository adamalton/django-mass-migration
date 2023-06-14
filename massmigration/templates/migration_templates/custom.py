from massmigration.migrations import BaseMigration


class Migration(BaseMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This is for use for migrations which are not stored in a folder called 'migrations' inside
    # an installed app.
    app_label: str = None

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
        raise NotImplementedError(
            "Replace this with your code. It should defer a task to perform the data changes and then call "
            "self.mark_as_finished() when done, or self.mark_as_errored() if failed."
        )
