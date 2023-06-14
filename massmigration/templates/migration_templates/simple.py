from massmigration.migrations import SimpleMigration


class Migration(SimpleMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This is for use for migrations which are not stored in a folder called 'migrations' inside
    # an installed app.
    app_label: str = None

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def operation(self):
        # If you cannot perform the operation within a single task, then you should use the 'mapper'
        # or 'custom' template instead.
        raise NotImplementedError(
            "Replace this with your code.. It should perform the entire migration operation. This must be "
            "complete-able within the memory and time limits of a single task."
        )
