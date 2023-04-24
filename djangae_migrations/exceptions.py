class MigrationError(Exception):
    """ Base exception class for migration related errors. """


class MigrationAlreadyStarted(MigrationError):
    pass


class DependentMigrationNotApplied(MigrationError):
    pass
