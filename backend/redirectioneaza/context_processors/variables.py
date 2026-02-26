from django.conf import settings
from django.http import HttpRequest


def main(_: HttpRequest) -> dict[str, dict[str, list[dict[str, str]]]]:
    return {
        "CONTACT_EMAIL_ADDRESS": settings.CONTACT_EMAIL_ADDRESS,
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
    }
