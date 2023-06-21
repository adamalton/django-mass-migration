# Standard library
import os

# Third party
from django.apps.registry import apps
from django.core.management.base import BaseCommand, CommandError
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template

# Mass Migration
from massmigration.constants import MIGRATIONS_FOLDER
from massmigration.loader import is_valid_migration_id, is_valid_migration_name

class Command(BaseCommand):
    # TODO: write this

    # 1. Get name from command line args.
    # 2. Get app name from command line args.
    # 3. Get template name from command line args. Should allow either:
    #    - The name of a template in our 'templates' folder, e.g. 'mapper'; or
    #    - A path to a custom template, e.g. `myapp/migration-templates/my-migration.py`
    # 4. Make sure 'massmigrations' folder exists in that app
    # 5. Check name doesn't already exist as a file (with extension) in that folder.
    # 6. Get highest numbered migration in that folder.
    # 7. Create file with next migration number.
    # 8. Use template to populate file with empty Migration class and `dependencies` set to previous migration.

    help = "Create a new mass-migration file."

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            help=(
                "Name of the app for which to create a migration. "
                "This must be an installed app in your project."
            ),
        )
        parser.add_argument(
            "migration_name",
            help=(
                "Name to give the migration file. "
                "This can only contain letters, numbers and underscores."
            ),
        )
        parser.add_argument(
            "--template",
            default="mapper",
            help=(
                "Which mapper template to use as the base. "
                "Must exist as a python file in massmigration/templates/migration_templates."
            ),
        )

    def handle(self, *args, **options):
        app_label = options["app_label"]
        migration_name = options["migration_name"]

        if not is_valid_migration_name(migration_name):
            raise CommandError(
                f"{migration_name} is not a valid migration name. "
                "Use letters, digits and underscores only."
            )

        try:
            template = get_template(f"migration_templates/{options['template']}.py")
        except TemplateDoesNotExist:
            raise CommandError(f"Couldn't find migration template '{options['template']}'.")

        app = apps.get_app_config(app_label)
        migrations_folder_path = os.path.join(app.path, MIGRATIONS_FOLDER)
        if not os.path.isdir(migrations_folder_path):
            os.mkdir(migrations_folder_path)

        existing_migrations = []
        for item in os.listdir(migrations_folder_path):
            if is_valid_migration_id(item.rstrip(".py")):
                existing_migrations.append(item)

        if existing_migrations:
            latest = sorted(existing_migrations, reverse=True)[0]
            highest_number = int(latest.split("_", 1)[0])
            dependencies = [(app_label, latest.rstrip(".py"))]
        else:
            highest_number = 0
            dependencies = []

        migration_number = highest_number + 1
        full_name = f"{migration_number:04d}_{migration_name}.py"

        context = {"dependencies": dependencies}
        rendered = template.render(context)
        migration_path = os.path.join(migrations_folder_path, full_name)
        with open(migration_path, "w") as file:
            file.write(rendered)

        self.stdout.write(f"Created new migration: {migration_path}")
