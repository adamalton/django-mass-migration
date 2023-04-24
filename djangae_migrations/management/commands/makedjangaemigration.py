from django.core.management.base import BaseCommand


class Command(BaseCommand):
    # TODO: write this

    # 1. Get name from command line args.
    # 2. Get app name from command line args.
    # 3. Get template name from command line args. Should allow either:
    #    - The name of a template in our 'templates' folder, e.g. 'mapper'; or
    #    - A path to a custom template, e.g. `myapp/migration-templates/my-migration.py`
    # 4. Make sure 'migrations' folder exists in that app
    # 5. Check name doesn't already exist as a file (with extension) in that folder.
    # 6. Get highest numbered migration in that folder.
    # 7. Create file with next migration number.
    # 8. Use template to populate file with empty Migration class and `dependencies` set to previous migration.
    pass
