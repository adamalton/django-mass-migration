Djangae Migrations
==================

This is a Django app which provides utilities for performing data migrations in App Engine applications built using
[Djangae](https://gitlab.com/potato-oss/djangae/djangae) and [Glcoudc](https://gitlab.com/potato-oss/google-cloud/django-gcloud-connectors/).

Similar to Django's built-in migration system, it allows you to define data migrations to be performed on the database,
and it allows you to then apply those migration operations to your database and it tracks which migrations have been applied and which haven't.

Unlike Django's built-in migration system, it provides a web based (rather than terminal based) interface for managing the migrations,
and it provides tools for applying migrations to the Cloud Datastore using long-running background tasks via Djangae and Gcloudc.
