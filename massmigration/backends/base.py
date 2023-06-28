from abc import ABC


class BackendBase(ABC):
    """ Abstract base class which defines the methods that a backend must implement. """

    def run_simple(self, migration):
        """ Run the wrapped_operation() method on the given SimpleMigration.
            For simple migrations, the wrapped_operation() method handles the calling of
            mark_as_started(), mark_as_errored() and mark_as_finished() for you.
            The backend just needs to hand off to whatever processor/task service it wants to in
            order to call wrapped_operation().
        """
        raise NotImplementedError

    def run_mapper(self, migration):
        """ Call migration.wrapped_operation(instance, attempt_uuid) for every instance returned by
            the get_queryset() method of the given MapperMigration.
            This MUST:
            * Call migration.mark_as_started() before performing the data operation.
            * Get the value of `migration.attempt_uuid` returned from `mark_as_started()` and pass
              it as the second argument to every call of `wrapped_operation()`.
            * Call migration.mark_as_finished() when the end of the queryset is reached.

            If `wrapped_operation()` returns False, it means that the migration has errored and
            iteration can be stopped. But continuing to iterate will do no harm.
        """
        raise NotImplementedError
