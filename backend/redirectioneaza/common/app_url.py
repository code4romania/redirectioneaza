from django.conf import settings
from django.http import HttpRequest


def build_uri(path: str, request: HttpRequest = None) -> str:
    if not request:
        return f"https://{settings.APEX_DOMAIN}{path}"

    return request.build_absolute_uri(path)
