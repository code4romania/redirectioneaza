import os
from pathlib import Path

from .constants import BASE_DIR
from .environment import env

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASE_ENGINE = env("DATABASE_ENGINE")

REMOTE_DATABASE_ENGINES = {
    "mysql": "django.db.backends.mysql",
    "postgres": "django.db.backends.postgresql",
}
if DATABASE_ENGINE in REMOTE_DATABASE_ENGINES.keys():
    DATABASES = {
        "default": {
            "ENGINE": REMOTE_DATABASE_ENGINES[DATABASE_ENGINE],
            "NAME": env("DATABASE_NAME"),
            "USER": env("DATABASE_USER"),
            "PASSWORD": env("DATABASE_PASSWORD"),
            "HOST": env("DATABASE_HOST"),
            "PORT": env("DATABASE_PORT"),
        }
    }
else:
    # create a sqlite database in the .db_sqlite directory
    sqlite_path = Path(os.path.join(BASE_DIR, ".db_sqlite", "db.sqlite3"))

    if not sqlite_path.exists():
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite_path.open("w") as f:
            pass

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.abspath(sqlite_path),
        }
    }


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
