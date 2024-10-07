from django.conf import settings


def environment_callback(_):
    environment = f"{settings.ENVIRONMENT} | {settings.VERSION_SUFFIX}"
    log_level = settings.DJANGO_LOG_LEVEL

    return environment, log_level
