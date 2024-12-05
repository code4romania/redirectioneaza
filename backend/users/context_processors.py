from django.conf import settings
from django.http import HttpRequest


def get_admin_properties(request: HttpRequest):
    user = request.user
    return {
        "is_admin": user.has_perm("users.can_view_old_dashboard"),
        "is_staff": user.is_staff,
        "SOCIALACCOUNT_ENABLED": settings.SOCIALACCOUNT_ENABLED,
        "SOCIALACCOUNT_ONLY": settings.SOCIALACCOUNT_ONLY,
    }
