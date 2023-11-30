# Standard library
import os
import shutil

# Third party
from django.apps.registry import apps
from django.core.management import execute_from_command_line
from django.test import TestCase

# Mass Migration
from massmigration.constants import MIGRATIONS_FOLDER


class MakeMassMigrationTestCase(TestCase):
    """ Tests for the 'makemassmigration' command. """

    def tearDown(self):
        super().tearDown()
        self.delete_massmigrations_folder()

    def migrations_folder_path(self, app_name="massmigration"):
        """ The expected folder path where the command will put the migration files. """
        app = apps.get_app_config(app_name)
        return os.path.join(app.path, MIGRATIONS_FOLDER)

    def delete_massmigrations_folder(self, app_name="massmigration"):
        """ Delete the folder which the command puts the migration files into. """
        path = self.migrations_folder_path(app_name)
        if os.path.exists(path):
            shutil.rmtree(path)

    def get_migration_file(self, file_name, app_name="massmigration"):
        """ Return the file contents of the given migration file. """
        file_path = os.path.join(self.migrations_folder_path(app_name), file_name)
        with open(file_path) as file:
            return file.read()

    def assert_migration_file_exists(self, file_name, app_name="massmigration"):
        file_path = os.path.join(self.migrations_folder_path(app_name), file_name)
        if not os.path.exists(file_path):
            self.fail(f"Migration file not found at {file_path}")

    def run_command(self, file_name, *args, app_name="massmigration"):
        execute_from_command_line([
            "django-admin",
            "makemassmigration",
            app_name,
            file_name,
            *args,
        ])

    def test_increments_numbers(self):
        self.run_command("first_migration")
        self.assert_migration_file_exists("0001_first_migration.py")
        self.run_command("second_migration")
        self.assert_migration_file_exists("0002_second_migration.py")

    def test_uses_correct_template(self):
        for index, (template, expected_base_class) in enumerate([
            ("simple", "SimpleMigration"),
            ("mapper", "MapperMigration"),
            ("custom", "BaseMigration"),
        ]):
            self.run_command("my_migration", "--template", template)
            file_contents = self.get_migration_file(f"000{index + 1}_my_migration.py")
            self.assertIn(f"\nclass Migration({expected_base_class}):\n", file_contents)
