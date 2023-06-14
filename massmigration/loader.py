# Standard library
import os
import re


def get_key_tuple(cls):
    """ Given a migration class, return the tuple of its (app_label, name). """
    raise NotImplementedError
    # TODO: finish this. Although it might become slightly obsolete when I build the rest of the
    # loading stuff

    if cls.app_label:
        app_label = cls.app_label
    else:
        folder = os.path.dirname(os.path.abspath("TODO"))
    filename = os.path.abspath("TODO")
    name = filename.replace(".py")
    assert is_valid_migration_id(name)
    return (app_label, name)


def is_valid_migration_name(name):
    return bool(re.match(r"^[a-z0-9_]+$", name))

def is_valid_migration_id(name):
    return bool(re.match(r"^\d{1,5}_[a-z0-9_]+$", name))
