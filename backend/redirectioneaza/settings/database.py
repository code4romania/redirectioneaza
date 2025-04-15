from .environment import env
import sys

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# If we’re running tests, point at a dedicated test DB on localhost
if "test" in sys.argv:
    DATABASES["default"].update(
        {
            "NAME": env("TEST_DATABASE_NAME", default="redirectioneaza_test"),
            "HOST": env("TEST_DATABASE_HOST", default="localhost"),
            "USER": env("TEST_DATABASE_USER", default=env("DATABASE_USER")),
            "PASSWORD": env("TEST_DATABASE_PASSWORD", default=env("DATABASE_PASSWORD")),
        }
    )
