from django.contrib.auth.decorators import user_passes_test


def superuser_required(login_url=None):
    """ Decorator for views that checks whether a user is a superuser. """

    def is_superuser(user):
        return user.is_superuser

    return user_passes_test(is_superuser, login_url=login_url)
