from django.utils.translation import gettext_lazy as _
from .environment import env

# Django Q2 — https://django-q2.readthedocs.io/en/stable/configure.html#configuration

Q_CLUSTER_WORKERS: int = env.int("DJANGO_Q_WORKERS_COUNT")
Q_CLUSTER_RECYCLE: int = env.int("DJANGO_Q_RECYCLE_RATE")
Q_CLUSTER_TIMEOUT: int = env.int("DJANGO_Q_TIMEOUT_SECONDS")
Q_CLUSTER_RETRY: int = Q_CLUSTER_TIMEOUT + (env.int("DJANGO_Q_RETRY_AFTER_TIMEOUT_SECONDS") or 1)
Q_CLUSTER_POLL: int = env.int("DJANGO_Q_POLL_SECONDS")

Q_CLUSTER = {
    "name": "redirect",
    "workers": Q_CLUSTER_WORKERS,
    "recycle": Q_CLUSTER_RECYCLE,
    "timeout": Q_CLUSTER_TIMEOUT,
    "retry": Q_CLUSTER_RETRY,
    "ack_failures": True,
    "max_attempts": 2,
    "compress": True,
    "save_limit": 200,
    "cpu_affinity": 1,
    "label": _("Background Tasks"),
    "orm": "default",
    "poll": Q_CLUSTER_POLL,
    "guard_cycle": 3,
    "catch_up": False,
}

IMPORT_METHOD = env.str("IMPORT_METHOD")
IMPORT_USE_BATCHES = env.bool("IMPORT_USE_BATCHES")
IMPORT_BATCH_SIZE = env.int("IMPORT_BATCH_SIZE")
