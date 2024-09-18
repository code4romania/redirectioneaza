from django.conf import settings
from django.http import HttpRequest


def is_admin(request: HttpRequest):
    return {
        "is_admin": request.user.has_perm("users.can_view_old_dashboard"),
        "is_staff": request.user.is_staff,
        "SOCIALACCOUNT_ENABLED": settings.SOCIALACCOUNT_ENABLED,
        "SOCIALACCOUNT_ONLY": settings.SOCIALACCOUNT_ONLY,
    }
