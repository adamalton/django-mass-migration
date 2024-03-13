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

    # Load the migration in bulk from every db to avoid a separate query for each one
    migration_records_by_db_alias = {
        db_alias: MigrationRecord.objects.using(db_alias).in_bulk()
        for db_alias in available_db_aliases
    }

    for migration in migrations:
        migration.records_map = OrderedDict()

        for db_alias in available_db_aliases:
            migration.records_map[db_alias] = {
                "is_allowed_on_db_alias": db_alias in migration.get_allowed_db_aliases(),
                "record": migration_records_by_db_alias[db_alias].get(migration.key, None)
            }

    context = {
        "migrations": migrations,
        "available_db_aliases": available_db_aliases,
    }
    return render(request, "massmigration/manage_migrations.html", context)


@superuser_required()
def run_migration(request, key, db_alias):
    """ Trigger the running of a migration. """
    migration = store.by_key.get(key)
    if not migration:
        raise Http404(f"Migration with key '{key}' not found.")

    record = migration.get_migration_record(db_alias)

    if record:
        messages.error(request, f"Migration '{key}' for db <{db_alias}> has already been started.")
        return redirect("massmigration_manage")
    try:
        migration.check_dependencies(db_alias)
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
        "db_alias": db_alias,
    }
    return render(request, "massmigration/run_migration.html", context)


@superuser_required()
def migration_detail(request, key, db_alias):
    """ View the details of a single migration. """
    # TODO(https://github.com/adamalton/django-mass-migration/issues/4):
    # The migration detail view should collate the state of the Migration
    # across all allowed_db_aliases.
    migration = store.by_key.get(key)
    if not migration:
        raise Http404(f"Migration with key {key} not found.")

    record = MigrationRecord.objects.using(db_alias).filter(key=key).first()
    dependencies = []
    dependency_keys = [MigrationRecord.key_from_name_tuple(x) for x in migration.dependencies]
    dependency_records_by_key = MigrationRecord.objects.using(db_alias).in_bulk(dependency_keys)
    for dep_key in dependency_keys:
        dependencies.append({
            "key": dep_key,
            "record": dependency_records_by_key.get(dep_key),
        })
    context = {
        "migration": migration,
        "record": record,
        "dependencies": dependencies,
        "db_alias": db_alias,
    }
    return render(request, "massmigration/migration_detail.html", context)


@superuser_required()
def delete_migration(request, key, db_alias):
    """ Delete a migration which has already started or has errored. """
    migration = store.by_key.get(key)
    if not migration:
        raise Http404(f"Migration with key {key} not found.")

    record = migration.get_migration_record(db_alias)

    if not record:
        messages.error(
            request,
            f"Can't delete migration '{key}' for db <{db_alias}> because no record for it exists. "
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
