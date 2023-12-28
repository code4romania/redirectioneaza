"""
Django settings for the redirectioneaza project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

import environ
import sentry_sdk
from django.utils import timezone

# Constants for memory sizes
KIBIBYTE = 1024
MEBIBYTE = KIBIBYTE * 1024
GIBIBYTE = MEBIBYTE * 1024
TEBIBYTE = GIBIBYTE * 1024

# Build paths inside the project like this: BASE_DIR / 'subdir'.
ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = os.path.abspath(os.path.join(ROOT, "backend"))


env = environ.Env(
    # set casting, default value
    # Django settings
    DEBUG=(bool, False),
    ENVIRONMENT=(str, "production"),
    # db settings
    DATABASE_ENGINE=(str, "sqlite3"),
    DATABASE_NAME=(str, "default"),
    DATABASE_USER=(str, "root"),
    DATABASE_PASSWORD=(str, ""),
    DATABASE_HOST=(str, "localhost"),
    DATABASE_PORT=(str, "3306"),
    # site settings
    APEX_DOMAIN=(str, "redirectioneaza.ro"),
    SITE_TITLE=(str, "redirectioneaza 3,5%"),
    DONATIONS_LIMIT_DATE=(str, "2016-05-25"),
    DONATIONS_LIMIT_TO_CURRENT_YEAR=(bool, True),
    DEFAULT_NGO_LOGO=(str, "https://storage.googleapis.com/redirectioneaza/logo_bw.png"),
    # security settings
    ALLOWED_HOSTS=(list, ["*"]),
    CORS_ALLOWED_ORIGINS=(list, []),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
    # zipping settings
    ZIPPY_URL=(str, "zippy:8000"),
    # email settings
    EMAIL_SEND_METHOD=(str, "async"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    EMAIL_HOST=(str, ""),
    EMAIL_PORT=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(str, ""),
    EMAIL_FAIL_SILENTLY=(bool, False),
    CONTACT_EMAIL_ADDRESS=(str, "no-reply@redirectioneaza.ro"),
    DEFAULT_FROM_EMAIL=(str, "email@example.com"),
    DEFAULT_RECEIVE_EMAIL=(str, "email@example.com"),
    NO_REPLY_EMAIL=(str, "noreply@example.com"),
    # django-q2 settings
    BACKGROUND_WORKERS_COUNT=(int, 1),
    # recaptcha settings
    CAPTCHA_PUBLIC_KEY=(str, ""),
    CAPTCHA_PRIVATE_KEY=(str, ""),
    CAPTCHA_REQUIRED_SCORE=(float, 0.5),
    CAPTCHA_VERIFY_URL=(str, "https://www.google.com/recaptcha/api/siteverify"),
    CAPTCHA_POST_PARAM=(str, "g-recaptcha-response"),
    # aws settings
    USE_S3=(bool, False),
    AWS_STORAGE_DEFAULT_BUCKET_NAME=(str, ""),
    AWS_STORAGE_PUBLIC_BUCKET_NAME=(str, ""),
    AWS_STORAGE_PRIVATE_BUCKET_NAME=(str, ""),
    AWS_DEFAULT_ACL=(str, ""),
    AWS_PUBLIC_ACL=(str, ""),
    AWS_PRIVATE_ACL=(str, ""),
    AWS_REGION_NAME=(str, ""),
    AWS_S3_REGION_NAME=(str, ""),
    # sentry
    SENTRY_DSN=(str, ""),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0),
    SENTRY_PROFILES_SAMPLE_RATE=(float, 0),
)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production
DEBUG = env.bool("DEBUG")
ENVIRONMENT = env.str("ENVIRONMENT")

# superuser/admin seed data
DJANGO_ADMIN_PASSWORD = env.str("DJANGO_ADMIN_PASSWORD", None)
DJANGO_ADMIN_EMAIL = env.str("DJANGO_ADMIN_EMAIL", None)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
APEX_DOMAIN = env.str("APEX_DOMAIN")

CSRF_HEADER_NAME = "HTTP_X_XSRF_TOKEN"
CSRF_COOKIE_NAME = "XSRF-TOKEN"

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS")

# Application definition
APPEND_SLASH = True

# some settings will be different if it's not running in a container (e.g., locally, on a Mac)
IS_CONTAINERIZED = env.bool("IS_CONTAINERIZED")

VERSION = env.str("VERSION", "edge")
REVISION = env.str("REVISION", "develop")

VERSION_SUFFIX = f"redirect@{VERSION}+{REVISION}"


if IS_CONTAINERIZED and VERSION == "edge" and REVISION == "develop":
    version_file = "/var/www/redirect/.version"
    if os.path.exists(version_file):
        with open(version_file) as f:
            VERSION, REVISION = f.read().strip().split("+")

# Sentry
if env.str("SENTRY_DSN"):
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
        release=VERSION_SUFFIX,
    )

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party apps:
    "storages",
    "django_q",
    # custom apps:
    "donations",
    "partners",
    "users",
]

if not env.bool("USE_S3"):
    INSTALLED_APPS.append("whitenoise.runserver_nostatic")


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "partners.middleware.PartnerDomainMiddleware",
]

ROOT_URLCONF = "redirectioneaza.urls"

TEMPLATES = [
    {
        # New templates for v2
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.abspath(os.path.join(BASE_DIR, "templates", "v2"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    {
        # The original v1 templates which use the Jinja engine
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [os.path.abspath(os.path.join(BASE_DIR, "templates", "v1"))],
        "APP_DIRS": False,
        "OPTIONS": {
            "environment": "redirectioneaza.jinja2.environment",
        },
    },
]

WSGI_APPLICATION = "redirectioneaza.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.abspath(os.path.join(BASE_DIR, ".db_sqlite", "db.sqlite3")),
    }
}

if env.str("DATABASE_ENGINE") == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env.str("DATABASE_NAME"),
            "USER": env.str("DATABASE_USER"),
            "PASSWORD": env.str("DATABASE_PASSWORD"),
            "HOST": env.str("DATABASE_HOST"),
            "PORT": env.str("DATABASE_PORT"),
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "redirect_cache_default",
    }
}


AUTH_USER_MODEL = "users.User"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Email settings
EMAIL_BACKEND = env.str("EMAIL_BACKEND")
EMAIL_SEND_METHOD = env.str("EMAIL_SEND_METHOD")

DEFAULT_RECEIVE_EMAIL = env.str("DEFAULT_RECEIVE_EMAIL")
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")
NO_REPLY_EMAIL = env.str("NO_REPLY_EMAIL")

EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_PORT = env.str("EMAIL_PORT")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")

EMAIL_FAIL_SILENTLY = env.bool("EMAIL_FAIL_SILENTLY")


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "ro"

TIME_ZONE = "Europe/Bucharest"

USE_I18N = True

USE_TZ = True


# Media & Static files storage
# https://docs.djangoproject.com/en/4.2/howto/static-files/

public_static_location = "static"
public_media_location = "media"
private_media_location = "media"

static_storage = "whitenoise.storage.CompressedStaticFilesStorage"
media_storage = "django.core.files.storage.FileSystemStorage"

STATIC_URL = f"{public_static_location}/"
MEDIA_URL = f"{public_media_location}/"

STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "static"))
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "media"))

DEV_DEPENDECIES_LOCATION = "bower_components"

STATICFILES_DIRS = [
    os.path.abspath(os.path.join(DEV_DEPENDECIES_LOCATION)),
    os.path.abspath(os.path.join("static_extras")),
]

default_storage_options = {}
public_storage_options = {}
private_storage_options = {}

if env.bool("USE_S3"):
    media_storage = "storages.backends.s3boto3.S3Boto3Storage"
    static_storage = "storages.backends.s3boto3.S3StaticStorage"

    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
    default_storage_options = {
        "bucket_name": (env.str("AWS_STORAGE_DEFAULT_BUCKET_NAME")),
        "default_acl": (env.str("AWS_DEFAULT_ACL")),
        "region_name": env.str("AWS_S3_REGION_NAME") or env.str("AWS_REGION_NAME"),
        "object_parameters": {"CacheControl": "max-age=86400"},
        "file_overwrite": False,
    }

    if aws_session_profile := env.str("AWS_S3_SESSION_PROFILE", default=None):
        default_storage_options["session_profile"] = aws_session_profile
    elif aws_access_key := env.str("AWS_ACCESS_KEY_ID", default=None):
        default_storage_options["access_key"] = aws_access_key
        default_storage_options["secret_key"] = env.str("AWS_SECRET_ACCESS_KEY")

    private_storage_options = deepcopy(default_storage_options)
    if private_acl := env.str("AWS_PRIVATE_ACL"):
        private_storage_options["default_acl"] = private_acl
    if bucket_name := env.str("AWS_STORAGE_PRIVATE_BUCKET_NAME"):
        private_storage_options["bucket_name"] = bucket_name

    public_storage_options = deepcopy(default_storage_options)
    if public_acl := env.str("AWS_PUBLIC_ACL"):
        public_storage_options["default_acl"] = public_acl
    if public_bucket_name := env.str("AWS_STORAGE_PUBLIC_BUCKET_NAME"):
        public_storage_options["bucket_name"] = public_bucket_name
    if custom_domain := env.str("AWS_S3_CUSTOM_DOMAIN", default=None):
        public_storage_options["custom_domain"] = custom_domain


STORAGES = {
    "default": {
        "BACKEND": media_storage,
        "LOCATION": private_media_location,
        "OPTIONS": default_storage_options,
    },
    "public": {
        "BACKEND": media_storage,
        "LOCATION": public_media_location,
        "OPTIONS": public_storage_options,
    },
    "staticfiles": {
        "BACKEND": static_storage,
        "LOCATION": public_static_location,
        "OPTIONS": public_storage_options,
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Global parameters

TITLE = env.str("SITE_TITLE")

DONATIONS_LIMIT = datetime.strptime(env.str("DONATIONS_LIMIT_DATE"), "%Y-%m-%d").date()
if env.bool("DONATIONS_LIMIT_TO_CURRENT_YEAR"):
    DONATIONS_LIMIT = date(timezone.now().year, DONATIONS_LIMIT.month, DONATIONS_LIMIT.day)

DONATIONS_LIMIT_MONTH_NAME = [
    "Ianuarie",
    "Februarie",
    "Martie",
    "Aprilie",
    "Mai",
    "Iunie",
    "Iulie",
    "August",
    "Septembrie",
    "Octombrie",
    "Noiembrie",
    "Decembrie",
][DONATIONS_LIMIT.month - 1]

START_YEAR = 2016

DEFAULT_NGO_LOGO = env.str("DEFAULT_NGO_LOGO")

LIST_OF_COUNTIES = [
    "Alba",
    "Arad",
    "Arges",
    "Bacau",
    "Bihor",
    "Bistrita-Nasaud",
    "Botosani",
    "Braila",
    "Brasov",
    "Buzau",
    "Calarasi",
    "Caras-Severin",
    "Cluj",
    "Constanta",
    "Covasna",
    "Dambovita",
    "Dolj",
    "Galati",
    "Giurgiu",
    "Gorj",
    "Harghita",
    "Hunedoara",
    "Ialomita",
    "Iasi",
    "Ilfov",
    "Maramures",
    "Mehedinti",
    "Mures",
    "Neamt",
    "Olt",
    "Prahova",
    "Salaj",
    "Satu Mare",
    "Sibiu",
    "Suceava",
    "Teleorman",
    "Timis",
    "Tulcea",
    "Valcea",
    "Vaslui",
    "Vrancea",
]
CONTACT_EMAIL_ADDRESS = env.str("CONTACT_EMAIL_ADDRESS")

# Django Q2
# https://django-q2.readthedocs.io/en/stable/brokers.html


Q_CLUSTER = {
    "name": "factory",
    "workers": env.int("BACKGROUND_WORKERS_COUNT"),
    "recycle": 100,
    "timeout": 900,  # A task must finish in less than 15 minutes
    "retry": 1200,  # Retry an unfinished tasks after 20 minutes
    "ack_failures": True,
    "max_attempts": 2,
    "compress": True,
    "save_limit": 200,
    "queue_limit": 4,
    "cpu_affinity": 1,
    "label": "Django Q2",
    "orm": "default",
    "poll": 2,
    "guard_cycle": 3,
    "catch_up": False,
}


# reCAPTCHA

CAPTCHA_PUBLIC_KEY = env.str("CAPTCHA_PUBLIC_KEY")
CAPTCHA_PRIVATE_KEY = env.str("CAPTCHA_PRIVATE_KEY")
CAPTCHA_REQUIRED_SCORE = env.float("CAPTCHA_REQUIRED_SCORE")

CAPTCHA_VERIFY_URL = env.str("CAPTCHA_VERIFY_URL")
CAPTCHA_POST_PARAM = env.str("CAPTCHA_POST_PARAM")

CAPTCHA_ENABLED = True if CAPTCHA_PUBLIC_KEY else False
