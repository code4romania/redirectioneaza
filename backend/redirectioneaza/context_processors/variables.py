from django.conf import settings
from django.http import HttpRequest


def main(_: HttpRequest) -> dict[str, dict[str, list[dict[str, str]]]]:
    return {
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
    }
