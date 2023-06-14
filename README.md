Django Mass Migration
=====================

This is a Django app which provides utilities for performing data migrations in App Engine applications built using
[Djangae](https://gitlab.com/potato-oss/djangae/djangae) and [Glcoudc](https://gitlab.com/potato-oss/google-cloud/django-gcloud-connectors/).

Similar to Django's built-in migration system, it allows you to define data migrations to be performed on the database,
and it allows you to then apply those migration operations to your database and it tracks which migrations have been applied and which haven't.

Unlike Django's built-in migration system, it is designed for performing long-running data modification tasks which run on Google Cloud Tasks,
and where there could be a significant amount of time between when the migration is started and when it's finished.
See [Concepts](#concepts).

Partly for that reason, and just for awesomeness, it provides a web based (rather than terminal based) interface for managing the migrations.


Installation
------------

1. Install the package: `pip install massmigration`
2. Add `massmigration` to `settings.INSTALLED_APPS`.


Creating A Migration
--------------------

To create a new migration, run the `makemassmigration` management command:

```python manage.py makemassmigration myapp my_migration_name```

This command has two required, positional arguments:

1. `app_label` - this should be the name of an installed app in your project.
2. `migration_name` - this should be the name that you want to give you migration.

The command also takes the following optional arguments:

* `--template` - this should be the name of one of the supplied templates in `massmigration/templates`, without the extension, e.g. `--template=mapper`. See [Migration Types](#migration-types).

A file will be created inside a folder called 'migrations' in your app, using the supplied migration name.
E.g. `myapp/migrations/001_my_migration.py`.
This is a blank slate for you to write your migration code in.


Migration Types
---------------

There are three broad types of migration for you to choose from.

### simple

TODO: explain this

### mapper

TODO: explain this

### custom

TODO: explain this


Applying Migrations
-------------------

There are two ways to apply a migration to the database:

### Via the Django Admin

1. Ensure that the Django admin is set up in your project.
2. Deploy your project, including the new migration file, to Google App Engine.
3. Go to the Django Admin site and under the Djangae Migrations app, select Migration Record.
4. Click the "Manage Migrations" button.
5. Next to your new migration, click "Run...".
6. Click "Run migration".
7. Wait for the migration to be listed as applied in the Migration Record list view, or check the Google Cloud Logging output for more detailed progress information.

### Programmatically

If you want to create your own system for applying migrations, you can use the API functions.
Or you will be able to, once I've written them.


Concepts
--------

### General approach

TODO: long-running migrations, errors, etc.

### Model State

TODO: Stuff about why there's no model history (apps/schema_editor).

### Workflow & Code Protection

TODO: Deployment workflow and use of enforcement utilities


Settings
--------

The following settings can be used:

#### `MASSMIGRATION_BACKEND`

This should be a dotted path string to the backend class that you want to use.


#### `MASSMIGRATION_TASK_QUEUE`

Used by the `DjangaeBackend`, this sets the Google Cloud Tasks queue name to be used for running migration tasks.


#### `MASSMIGRATION_RECORD_CACHE_TIMEOUT`

You're unlikely to need this.
It sets the time for caching MigrationRecords for the purpose of checking a migration's status during mapper operations.
