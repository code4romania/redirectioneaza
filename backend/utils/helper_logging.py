import logging

from django.conf import settings


def setup_logger(name: str):
    logger = logging.getLogger(name)

    log_level: str = settings.DJANGO_LOG_LEVEL if not settings.CUSTOM_LOG_LEVEL else settings.CUSTOM_LOG_LEVEL
    logger.setLevel(log_level.upper())

    return logger
