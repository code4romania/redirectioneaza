from typing import Dict, List

from django.conf import settings
from django.http import HttpRequest


def main(_: HttpRequest) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    return {
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
    }
