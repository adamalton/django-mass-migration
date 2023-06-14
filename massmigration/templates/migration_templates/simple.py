from massmigration.migrations import SimpleMigration


class Migration(SimpleMigration):
    """ YOUR DESCRIPTION HERE. This will appear in the Django admin. """

    # This can be set to make a migration run on a specific backend, rather than the one that's
    # that's specified in the Django settings
    backend: str = None

    dependencies = [{% for dependency in dependencies %}
        ("{{dependency.0}}", "{{dependency.1}}"),{% endfor %}
    ]

    def operation(self):

        # PUT YOUR CODE HERE.
        # It should perform the entire migration operation in this single step.
        # This must be complete-able within the memory and time limits of the backend.
        # If you cannot perform the operation within a single operation, then you should use the
        # 'mapper' or 'custom' template instead.

        raise NotImplementedError
