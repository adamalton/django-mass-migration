from massmigration.migrations import BaseMigration


class Migration(BaseMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def start(self):
        self.check_dependencies()
        self.mark_as_started()
        raise NotImplementedError(
            "Replace this with your code.. It should defer a task to perform the data changes and then call "
            "self.mark_as_finished() when done, or self.mark_as_errored() if failed."
        )
