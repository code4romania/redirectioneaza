import hashlib
import os

from .environment import env

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret
SECRET_KEY = env.str("SECRET_KEY")
SECRET_KEY_HASH = hashlib.blake2s(SECRET_KEY.encode()).hexdigest()
OLD_SESSION_KEY = env.str("OLD_SESSION_KEY")

# SECURITY WARNING: don't run with debug turned on in production
DEBUG = env.bool("DEBUG")
ENVIRONMENT = env.str("ENVIRONMENT")

DATA_UPLOAD_MAX_NUMBER_FIELDS = env.int("DATA_UPLOAD_MAX_NUMBER_FIELDS")

# Proxy HOST & Scheme headers
USE_X_FORWARDED_HOST = env.bool("USE_PROXY_FORWARDED_HOST", False)
if proxy_ssl_header_name := env.str("PROXY_SSL_HEADER", ""):
    SECURE_PROXY_SSL_HEADER = (proxy_ssl_header_name, "https")

# superuser/admin seed data
DJANGO_ADMIN_PASSWORD = env.str("DJANGO_ADMIN_PASSWORD", None)
DJANGO_ADMIN_EMAIL = env.str("DJANGO_ADMIN_EMAIL", None)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
APEX_DOMAIN = env.str("APEX_DOMAIN")
BASE_WEBSITE = env.str("BASE_WEBSITE")

CSRF_HEADER_NAME = "HTTP_X_XSRF_TOKEN"
CSRF_COOKIE_NAME = "XSRF-TOKEN"

SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE")

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS")

# Application definition
APPEND_SLASH = True

# some settings will be different if it's not running in a container (e.g., locally, on a Mac)
IS_CONTAINERIZED = env.bool("IS_CONTAINERIZED")

DEFAULT_REVISION_STRING = "dev"


VERSION = env.str("VERSION", "edge")
REVISION = env.str("REVISION", DEFAULT_REVISION_STRING)
REVISION = REVISION[:7]

if IS_CONTAINERIZED and VERSION == "edge" and REVISION == DEFAULT_REVISION_STRING:
    version_file = "/var/www/redirect/.version"
    if os.path.exists(version_file):
        with open(version_file) as f:
            VERSION, REVISION = f.read().strip().split("+")

VERSION_SUFFIX = f"{VERSION}+{REVISION}"
VERSION_LABEL = f"redirect@{VERSION_SUFFIX}"


# Application definition

INSTALLED_APPS = [
    "unfold",  # this must be loaded before django.contrib.admin
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party apps:
    "storages",
    "django_q",
    "django_recaptcha",
    "django_vite",
    "import_export",
    "tinymce",
    # authentication
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.amazon_cognito",
    # custom apps:
    "donations",
    "partners",
    "users",
    "importer",
    "frequent_questions",
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
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # this is the default
    "allauth.account.auth_backends.AuthenticationBackend",
]

ROOT_URLCONF = "redirectioneaza.urls"

WSGI_APPLICATION = "redirectioneaza.wsgi.application"


# User & Auth
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
