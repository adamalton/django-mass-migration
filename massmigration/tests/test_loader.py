# Third party
from django.test import TestCase

# Mass Migration
from massmigration.loader import (
    is_valid_migration_id,
    is_valid_migration_name,
    migration_id_from_filename,
)

class LoaderTestCase(TestCase):
    """ Tests for the 'loader.py' module. """

    def test_is_valid_migration_id(self):
        """ Test the `is_valid_migration_id` function. """
        for migration_id, expect_valid in [
            ("0023_valid_name", True),
            ("0023_dots_not_allowed.html", False),
            ("no_leading_zeros", False),
        ]:
            self.assertEqual(is_valid_migration_id(migration_id), expect_valid)

    def test_is_valid_migration_name(self):
        """ Test the `is_valid_migration_name` function. """
        for name, expect_valid in [
            ("valid_name_here", True),
            ("hyphens-not-allowed", False),
            ("dots.not.allowed", False),
        ]:
            self.assertEqual(is_valid_migration_name(name), expect_valid)

    def test_migration_id_from_filename(self):
        """ Test the `migration_id_from_filename` function. """
        for filename, expected_id in [
            ("0001_my_migration.py", "0001_my_migration"),
            ("0001_my_migration.html", None),
            ("__init__.py", None),
        ]:
            self.assertEqual(migration_id_from_filename(filename), expected_id)
