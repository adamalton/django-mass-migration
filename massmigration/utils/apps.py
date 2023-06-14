from django.apps.registry import apps


def get_app_label_choices():
    return [(app.label, app.label) for app in apps.get_app_configs()]
