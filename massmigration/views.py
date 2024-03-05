# Third party
from collections import OrderedDict
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

# Mass Migration
from massmigration.exceptions import DependentMigrationNotApplied
from massmigration.loader import store
from massmigration.migrations import get_all_db_aliases
from massmigration.models import MigrationRecord
from massmigration.utils.permissions import superuser_required


@superuser_required()
def manage_migrations(request):
    """ A page to manage mass migrations. """
    migrations = store.all
    available_db_aliases = get_all_db_aliases()
    # Load the migration records in one query to avoid a separate query for each one

    migration_records_by_db_alias = OrderedDict([
        (db_alias, MigrationRecord.objects.in_bulk().using(db_alias))
        for db_alias in available_db_aliases
    ])

    for migration in migrations:
        migration.records_map = OrderedDict([
            (db_alias, migration_records_by_db_alias.get(db_alias, None))
            for db_alias in migration.get_allowed_database_aliases()
        ])

    context = {
        "migrations": migrations,
        "available_db_aliases": available_db_aliases,
    }
    return render(request, "massmigration/manage_migrations.html", context)


@superuser_required()
def run_migration(request, key):
    """ Trigger the running of a migration. """
    db_alias = request.GET.get("db_alias", None)
    migration = store.by_key.get(key)
    record = migration.get_migration_record(db_alias)
    if not migration:
        raise Http404(f"Migration with key '{key}' not found.")
    if record:
        messages.error(request, f"Migration '{key}' has already been started.")
        return redirect("massmigration_manage")
    try:
        migration.check_dependencies()
    except DependentMigrationNotApplied as error:
        messages.error(request, str(error))
        return redirect("massmigration_manage")

    if request.method == "POST":
        migration.launch(db_alias)
        messages.success(request, f"Migration '{key}' started.")
        return redirect("massmigration_manage")

    # else...
    context = {
        "migration": migration,
    }
    return render(request, "massmigration/run_migration.html", context)


@superuser_required()
def migration_detail(request, key):
    """ View the details of a single migration. """
    migration = store.by_key.get(key)

    dependencies_by_db_alias = {}
    dependency_keys = [MigrationRecord.key_from_name_tuple(x) for x in migration.dependencies]

    migration_records_by_db_alias = {
        db_alias: MigrationRecord.objects.in_bulk((dependency_keys).using(db_alias))
        for db_alias in migration.get_allowed_database_aliases()
    }

    for db_alias in migration.get_allowed_database_aliases():
        dependency_records_by_key = migration_records_by_db_alias[db_alias]
        dependencies_by_db_alias[db_alias] = []
        for dep_key in dependency_keys:
            dependencies_by_db_alias[db_alias].append({
                "key": dep_key,
                "record": dependency_records_by_key.get(dep_key),
            })

    context = {
        "migration": migration,
        "records_by_db_alias": migration_records_by_db_alias,
        "dependencies_by_db_alias": dependencies_by_db_alias,
    }
    return render(request, "massmigration/migration_detail.html", context)


@superuser_required()
def delete_migration(request, key):
    """ Delete a migration which has already started or has errored. """
    migration = store.by_key.get(key)
    db_alias = request.GET.get("db_alias", None)

    record = migration.get_migration_record(db_alias)
    if not migration:
        raise Http404(f"Migration with key {key} for db {db_alias} not found.")
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
        "db_alias": db_alias,
    }
    return render(request, "massmigration/delete_migration.html", context)
