from django.templatetags.static import static
from django.urls import reverse

from django.conf import settings
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": static,
            "url": reverse,
            "bower_components": settings.DEV_DEPENDECIES_LOCATION,
            "DEV": settings.DEV,
            "PRODUCTION": settings.PRODUCTION,
            "title": settings.TITLE,
            "language": "ro",
            "base_url": "/",
            "months": settings.MONTH_NAMES,
            "captcha_public_key": settings.CAPTCHA_PUBLIC_KEY,
            "errors": None,
        }
    )
    return env
