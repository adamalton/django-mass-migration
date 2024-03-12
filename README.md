Django Mass Migration
=====================

A Django app which provides utilities for performing data operations on (optionally) large datasets.

Similar to Django's built-in migration system, it allows you to define data migrations to be performed on the database,
and to apply those migration operations to your database, and it tracks which migrations have been applied and which haven't.

Unlike Django's built-in migration system, it is designed for performing long-running data modification tasks
where there could be a significant amount of time between when the migration is started and when it's finished.
See [Concepts](#concepts).
It is particularly useful for schemaless databases where Django's normal concept of schema changes doesn't apply.

Due to the expectation that migrations maybe be long-running, and just for awesomeness, it provides a web based (rather than terminal based) interface for managing the migrations.

The actual running of the operations can be done on a "backend" of your choosing, e.g. a task queue.
A backend for running migration operations on [Djangae](https://gitlab.com/potato-oss/djangae/djangae) with [Glcoudc](https://gitlab.com/potato-oss/google-cloud/django-gcloud-connectors/) is bundled with the app.


Installation
------------

1. Install the package: `pip install django-mass-migration`
2. Add `massmigration` to `settings.INSTALLED_APPS`.
3. Add  `path("migrations/", include("massmigration.urls"))` to your root urlconf.
4. If you're using the bundled backend, set `settings.MASSMIGRATION_TASK_QUEUE` to a Google Cloud Tasks queue name.


Creating A Migration
--------------------

To create a new migration, run the `makemassmigration` management command:

```python manage.py makemassmigration myapp my_migration_name```

This command has two required, positional arguments:

1. `app_label` - this should be the name of an installed app in your project.
2. `migration_name` - this should be the name that you want to give you migration.

The command also takes the following optional arguments:

* `--template` - this should be the name of one of the supplied templates in `massmigration/templates/migration_templates`, without the extension, e.g. `--template=mapper`. See [Migration Types](#migration-types). The default is `mapper`.

A file will be created inside a folder called 'massmigrations' in your app, using the supplied migration name.
E.g. `myapp/massmigrations/001_my_migration.py`.
This is a blank slate for you to write your migration code in.


Migration Types
---------------

There are three broad types of migration for you to choose from.

### simple

This is for a migration which is just a single Python function.
It's intended for small operations which you know your backend can perform in one step.

### mapper

This is for mapping a function over the instances of a Django queryset.
You define a queryset and an `operation` function, and the migration will call that function on each object in the queryset.

The backend must be able to handle iterating over the queryset.
The bundled DjangaeBackend can handle almost infinite sized querysets.

### custom

If you want to take matters into your own hands you can write an entirely custom migration.
These can still be tracked the same as the other operations, but the implementation of what your migration
does and how your the backend handles it are up to you.

Running with Multiple DBs
-------------------
If your project connects to multiple databases it is possible to run your migrations against each database individually.
The migrations are not forced on a specific DB but rather the `db_alias` is passed to both to `get_queryset(db_alias)` (for mappers migrations) and `operation` (for simple migrations) giving control back to the developer to customise what is retrieved for the migration.

By default a migration can be run on any available database. That can be customised but setting `allowed_db_aliases` on the migration class.


Applying Migrations
-------------------

There are two ways to apply a migration to the database:

### Via the Web UI

1. Optionally: ensure that the Django admin is set up in your project.
2. Deploy your project, including the new migration file.
3. Either:
    - Go to the Django Admin site and under Mass Migrations -> Migration Record, click the "Manage Migrations" button; or
    - Go directly to the URL of `reverse("massmigration_manage")` whatever path you've configured that to be on.
5. Next to your new migration, click "Run...".
6. Click "Run migration".
7. Wait for the migration to be listed as applied in the Migration Record list view, or check the logging from your backend.

### Programmatically

If you want to create your own system for applying migrations, you can use the API functions.
Or you will be able to, once I've written them.


Protecting Code Which Requires Migrations
-----------------------------------------

Sometimes in the development cycle of your application, you will want to ensure that a particular migration has been run,
usually when you've added new code which expects the migration to have been applied before the code is run.

To handle this, Mass Migration provides the following utilities:

#### `massmigration.enforcement.requires_migration`

This is a function decorator which ensures that the function cannot be executed until the specified migration has been applied.
For example:

```python
@requires_migration(("myapp", "0001_my_migration"))
def my_function():
	...
```


This will raise `massmigration.exceptions.RequiredMigrationNotApplied` if the function is called before the migration is applied.

### Multiple DBs Support
When running on multiple databases, by default, the utilities assume that the migration must have been applied on all the databases specified by the Migration's `allowed_db_aliases` attribute.
To customise that behaviour the decorators accept an optional `db_aliases` list to specify a subset of the aliases allowed for the migration and require only those to have been applied.

```python
@requires_migration(("myapp", "0001_my_migration"), db_aliases=["my_db_alias"])
def my_function():
	...
```

### Notes:
* If the migration _is_ applied, then this will cache that fact, so it will only query the database the first time the function is called.
* The migration identifier can either be a tuple of `(app_label, migration_name)` or can be a string of `"app_label:migration_name"`.
* There is an optional second argument `skip_in_tests`, which defaults to `True`.


#### `massmigration.enforcement.view_requires_migration`

This is the same as `requires_migration` but for decorating a view function.
If the specified migration is not applied then the view will return a 503 response.



Concepts
--------

### General approach

TODO: long-running migrations, errors, etc.
Why long-running migrations are not run as part of the deployment process (because they take too long and you don't want to take your site down while they run).

### Model State

TODO: Stuff about why there's no model history (apps/schema_editor).

### Workflow & Code Protection

TODO: Deployment workflow and use of enforcement utilities


Settings
--------

The following settings can be used:

#### `MASSMIGRATION_BACKEND`

This should be a dotted path string to the backend class that you want to use.
The default is `"massmigration.backends.djangae.DjangaeBackend"`,
which works with SQL, Google Cloud Datastore and Firestore databases.


#### `MASSMIGRATION_TASK_QUEUE`

Used by the `DjangaeBackend`, this sets the Google Cloud Tasks queue name to be used for running migration tasks.


#### `MASSMIGRATION_RECORD_CACHE_TIMEOUT`

You're unlikely to need this.
It sets the time for caching MigrationRecords for the purpose of checking a migration's status during mapper operations.
