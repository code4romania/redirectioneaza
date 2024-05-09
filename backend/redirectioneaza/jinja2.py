from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

from donations.templatetags.url_extras import apex_reverse


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": static,
            "reverse": reverse,
            "apex_reverse": apex_reverse,
            "bower_components": settings.DEV_DEPENDECIES_LOCATION,
            "DEV": settings.ENVIRONMENT == "development",
            "PRODUCTION": settings.ENVIRONMENT == "production",
            "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
            "APEX_DOMAIN": settings.APEX_DOMAIN,
            "title": settings.TITLE,
            "language": "ro",
            "base_url": "/",
            "month_limit": settings.DONATIONS_LIMIT_MONTH_NAME,
            "captcha_public_key": settings.RECAPTCHA_PUBLIC_KEY,
            "errors": None,
        }
    )
    return env
