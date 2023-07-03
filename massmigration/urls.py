from django.urls import path

from . import views


urlpatterns = [
    path("manage/", views.manage_migrations, name="massmigration_manage"),
    path("run/<str:key>/", views.run_migration, name="massmigration_run"),
    path("detail/<str:key>/", views.migration_detail, name="massmigration_detail"),
    path("delete/<str:key>/", views.delete_migration, name="massmigration_delete"),
]
