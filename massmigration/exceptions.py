from django.db.utils import ConnectionDoesNotExist


class MigrationError(Exception):
    """ Base exception class for migration related errors. """


class MigrationAlreadyStarted(MigrationError):
    pass


class DependentMigrationNotApplied(MigrationError):
    """ Error for when trying to apply a migration which depends on another migration, and that
        other migration has not yet been applied.
    """
    pass


class RequiredMigrationNotApplied(Exception):
    """ Error for when a block of code which is marked as requiring a particular migration is being
        tried to run when that migration is not yet applied.
    """
    pass


class CannotRunOnDB(Exception):
    """ Error for when a migration can't be run on a specified connection.
    """
    pass


class DbAliasNotAllowed(ConnectionDoesNotExist):
    """ Error for when an invalid db_alias is provided.
    """
    pass
