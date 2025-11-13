from django.conf import settings
from django.http import HttpRequest


def main(_: HttpRequest) -> dict[str, bool]:
    return {
        "enable_multiple_forms": settings.ENABLE_MULTIPLE_FORMS,
        "enable_byof": settings.ENABLE_BYOF,
        "enable_csv_download": settings.ENABLE_CSV_DOWNLOAD,
    }
