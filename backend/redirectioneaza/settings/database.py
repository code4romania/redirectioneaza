import sys

from .environment import env

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DATABASE_NAME"),
        "USER": env.str("DATABASE_USER"),
        "PASSWORD": env.str("DATABASE_PASSWORD"),
        "HOST": env.str("DATABASE_HOST"),
        "PORT": env.str("DATABASE_PORT"),
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# If we’re running tests, point at a dedicated test DB if specified
if sys.argv[1:2] == ["test"]:
    DATABASES["default"].update(
        {
            "NAME": env.str("TEST_DATABASE_NAME", env.str("DATABASE_NAME")),
            "HOST": env.str("TEST_DATABASE_HOST", env.str("DATABASE_HOST")),
            "USER": env.str("TEST_DATABASE_USER", env.str("DATABASE_USER")),
            "PASSWORD": env.str("TEST_DATABASE_PASSWORD", env.str("DATABASE_PASSWORD")),
        }
    )
