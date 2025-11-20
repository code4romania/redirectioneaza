import sentry_sdk

from .base import ENVIRONMENT, VERSION_LABEL
from .environment import env

# Sentry
ENABLE_SENTRY = True if env.str("SENTRY_DSN") else False
if ENABLE_SENTRY:
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE"),
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=env.float("SENTRY_PROFILES_SAMPLE_RATE"),
        environment=ENVIRONMENT,
        release=VERSION_LABEL,
    )


# Logging
DJANGO_LOG_LEVEL = env.str("LOG_LEVEL").upper()
DJANGO_Q_LOG_LEVEL = env.str("LOG_LEVEL") or DJANGO_LOG_LEVEL

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": DJANGO_LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": True,
        },
        "django-q": {
            "handlers": ["console"],
            "level": DJANGO_Q_LOG_LEVEL,
            "propagate": True,
        },
    },
}

# Auditlog configuration

AUDITLOG_EXPIRY_DAYS = env.int("AUDITLOG_EXPIRY_DAYS")
AUDITLOG_INCLUDE_ALL_MODELS = False
