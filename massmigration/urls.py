from django.urls import path

from . import views


urlpatterns = [
    path("manage/", views.manage_migrations, name="massmigration_manage"),
    path("run/<str:key>/<str:db_alias>/", views.run_migration, name="massmigration_run"),
    path("detail/<str:key>/<str:db_alias>/", views.migration_detail, name="massmigration_detail"),
    path("delete/<str:key>/<str:db_alias>/", views.delete_migration, name="massmigration_delete"),
]
