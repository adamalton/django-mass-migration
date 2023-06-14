# Standard library
import os
import re

# Third party
from django.apps.registry import apps
from django.utils.module_loading import import_string

# Mass Migration
from .constants import MIGRATIONS_FOLDER


class MigrationsStore:
    """ Stores a cache of the installed migrations to save us loading them from the filesystem
        repeatedly. Also allows us to access them by key.
    """

    def __init__(self):
        self._loaded = False
        self._all = []
        self._by_key = {}

    @property
    def all(self):
        if not self._loaded:
            self.load()
        return self._all

    @property
    def by_key(self):
        if not self._loaded:
            self.load()
        return self._by_key

    def load(self):
        """ Load all the migration instances from all migration files found in installed apps. """
        for app_config in apps.get_app_configs():
            migrations_path = os.path.join(app_config.path, MIGRATIONS_FOLDER)
            if os.path.isdir(migrations_path):
                items = os.listdir(migrations_path)
                for item in sorted(items):
                    if is_valid_migration_id(item.rstrip(".py")):
                        migration = load_migration(app_config, item)
                        self._all.append(migration)
                        self._by_key[migration.key] = migration
        self._loaded = True


store = MigrationsStore()


def is_valid_migration_name(name):
    return bool(re.match(r"^[a-z0-9_]+$", name))

def is_valid_migration_id(name):
    return bool(re.match(r"^\d{1,5}_[a-z0-9_]+$", name))


def load_migration(app_config, filename):
    """ Return in instance of the migration class from the given filename from the given app_config.
    """
    module_str = app_config.name
    migration_name = filename.rstrip(".py")
    class_path_str = f"{module_str}.{MIGRATIONS_FOLDER}.{migration_name}.Migration"
    cls = import_string(class_path_str)
    app_label = app_config.label
    instance = cls(app_label, migration_name)
    return instance
