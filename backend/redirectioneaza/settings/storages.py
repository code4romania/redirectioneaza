import os
from copy import deepcopy
from typing import Any

from .constants import BASE_DIR
from .environment import env

# Media & Static files storage
# https://docs.djangoproject.com/en/4.2/howto/static-files/

static_static_location = "static"
public_media_location = "media"
private_media_location = "media"

static_storage = "whitenoise.storage.CompressedStaticFilesStorage"
media_storage = "django.core.files.storage.FileSystemStorage"

STATIC_URL = f"{static_static_location}/"
MEDIA_URL = f"{public_media_location}/"

STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "static"))
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "media"))

STATICFILES_DIRS = [
    os.path.abspath(os.path.join("static_extras")),
]

default_storage_options = {}

public_storage_options = {}
static_storage_options = {}

if env.bool("USE_S3"):
    media_storage = "storages.backends.s3boto3.S3Boto3Storage"
    static_storage = "storages.backends.s3boto3.S3StaticStorage"

    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
    default_storage_options = {
        "bucket_name": env.str("AWS_S3_STORAGE_DEFAULT_BUCKET_NAME"),
        "default_acl": env.str("AWS_S3_DEFAULT_ACL"),
        "region_name": env.str("AWS_S3_REGION_NAME") or env.str("AWS_REGION_NAME"),
        "object_parameters": {"CacheControl": "max-age=86400"},
        "file_overwrite": False,
        "signature_version": env.str("AWS_S3_SIGNATURE_VERSION"),
        "addressing_style": env.str("AWS_S3_ADDRESSING_STYLE"),
    }

    # Authentication, if not using IAM roles
    if aws_session_profile := env.str("AWS_S3_SESSION_PROFILE", default=None):
        default_storage_options["session_profile"] = aws_session_profile
    elif aws_access_key := env.str("AWS_ACCESS_KEY_ID", default=None):
        default_storage_options["access_key"] = aws_access_key
        default_storage_options["secret_key"] = env.str("AWS_SECRET_ACCESS_KEY")

    # Additional default configurations
    if default_prefix := env.str("AWS_S3_DEFAULT_PREFIX", default=None):
        default_storage_options["location"] = default_prefix
    if custom_domain := env.str("AWS_S3_DEFAULT_CUSTOM_DOMAIN", default=None):
        public_storage_options["custom_domain"] = custom_domain

    # Public storage options
    public_storage_options = deepcopy(default_storage_options)
    if public_acl := env.str("AWS_S3_PUBLIC_ACL"):
        public_storage_options["default_acl"] = public_acl
    if public_bucket_name := env.str("AWS_S3_STORAGE_PUBLIC_BUCKET_NAME"):
        public_storage_options["bucket_name"] = public_bucket_name
    if public_prefix := env.str("AWS_S3_PUBLIC_PREFIX", default=None):
        public_storage_options["location"] = public_prefix
    if custom_domain := env.str("AWS_S3_PUBLIC_CUSTOM_DOMAIN", default=None):
        public_storage_options["custom_domain"] = custom_domain

    static_storage_options = deepcopy(public_storage_options)
    if static_acl := env.str("AWS_S3_STATIC_ACL"):
        static_storage_options["default_acl"] = static_acl
    if static_bucket_name := env.str("AWS_S3_STORAGE_STATIC_BUCKET_NAME"):
        static_storage_options["bucket_name"] = static_bucket_name
    if static_prefix := env.str("AWS_S3_STATIC_PREFIX", default=None):
        static_storage_options["location"] = static_prefix
    if custom_domain := env.str("AWS_S3_STATIC_CUSTOM_DOMAIN", default=None):
        static_storage_options["custom_domain"] = custom_domain


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
        "LOCATION": static_static_location,
        "OPTIONS": static_storage_options,
    },
}


# Django Vite config

# Where ViteJS assets are built
django_vite_assets_path = os.path.abspath("dist")  # noqa
django_vite_sources_dir = os.path.abspath("assets")  # noqa

django_vite_dev_mode = env.bool("DJANGO_VITE_DEV_MODE")
django_vite_settings: dict[str, Any] = {
    "dev_mode": django_vite_dev_mode,
    "manifest_path": os.path.join(django_vite_assets_path, "manifest.json"),
}

IS_CONTAINERIZED = env.bool("IS_CONTAINERIZED")

if IS_CONTAINERIZED:
    # Where ViteJS assets are built
    STATIC_ROOT = os.path.abspath(os.path.join(os.sep, "var", "www", "redirect", "backend", "static"))
    MEDIA_ROOT = os.path.abspath(os.path.join(os.sep, "var", "www", "redirect", "backend", "media"))


# If we should use HMR or not
if django_vite_dev_mode:
    django_vite_settings["dev_server_port"] = env.int("DJANGO_VITE_DEV_SERVER_PORT")
    django_vite_settings["dev_server_host"] = env.str("DJANGO_VITE_DEV_SERVER_HOST")
    STATICFILES_DIRS.append(django_vite_sources_dir)
else:
    STATICFILES_DIRS.append(django_vite_assets_path)

DJANGO_VITE: dict[str, dict] = {
    "default": django_vite_settings,
}
