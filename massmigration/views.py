# Third party
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

# Mass Migration
from massmigration.exceptions import DependentMigrationNotApplied
from massmigration.loader import store
from massmigration.models import MigrationRecord
from massmigration.utils.permissions import superuser_required


@superuser_required()
def manage_migrations(request):
    """ A page to manage mass migrations. """
    migrations = store.all
    # Load the migration records in one query to avoid a separate query for each one
    records_by_key = MigrationRecord.objects.in_bulk()
    for migration in migrations:
        migration.record = records_by_key.get(migration.key)
    context = {
        "migrations": migrations,
    }
    return render(request, "massmigration/manage_migrations.html", context)


@superuser_required()
def run_migration(request, key):
    """ Trigger the running of a migration. """
    migration = store.by_key.get(key)
    record = MigrationRecord.objects.filter(key=key).first()
    if not migration:
        raise Http404(f"Migration with key {key} not found.")
    if record:
        messages.error(request, f"Migration with key {key} has already been started.")
        return redirect("massmigration_manage")
    try:
        migration.check_dependencies()
    except DependentMigrationNotApplied as error:
        messages.error(request, str(error))
        return redirect("massmigration_manage")

    if request.method == "POST":
        migration.launch()
        messages.success(request, f"Migration '{key}' started.")
        return redirect("massmigration_manage")

    # else...
    context = {
        "migration": migration,
    }
    return render(request, "massmigration/run_migration.html", context)



@superuser_required()
def delete_migration(request, key):
    """ Delete a migration which has already started or has errored. """
    migration = store.by_key.get(key)
    record = MigrationRecord.objects.filter(key=key).first()
    if not migration:
        raise Http404(f"Migration with key {key} not found.")
    if not record:
        messages.error(
            request,
            f"Can't delete migration '{key}' because no record for it exists. "
            "Maybe you deleted it already?"
        )
        return redirect("massmigration_manage")

    if request.method == "POST":
        record.delete()
        messages.success(request, f"Deleted record for migration '{key}")
        return redirect("massmigration_manage")

    # else...
    context = {
        "migration": migration,
    }
    return render(request, "massmigration/delete_migration.html", context)
