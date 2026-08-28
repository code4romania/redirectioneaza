import os

from .path_constants import BASE_DIR

TEMPLATES = [
    {
        # New templates for v2
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.abspath(os.path.join(BASE_DIR, "templates", "v3")),
            os.path.abspath(os.path.join(BASE_DIR, "templates", "v2")),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "redirectioneaza.context_processors.feature_flags.main",
                "redirectioneaza.context_processors.headers.main",
                "redirectioneaza.context_processors.variables.main",
                "partners.context_processors.custom_subdomain",
                "users.context_processors.get_admin_properties",
                "donations.context_processors.default_ngo_logo",
            ],
        },
    },
]
