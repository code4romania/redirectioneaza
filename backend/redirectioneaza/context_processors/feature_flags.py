from typing import Dict

from django.conf import settings
from django.http import HttpRequest


def main(_: HttpRequest) -> Dict[str, bool]:
    return {
        "enable_multiple_forms": settings.ENABLE_MULTIPLE_FORMS,
    }
