from django.conf import settings
from django.http import HttpRequest


def get_admin_properties(request: HttpRequest):
    try:
        user = request.user
    except AttributeError:
        user = None

    return {
        "is_admin": user.has_perm("users.can_view_old_dashboard") if user else False,
        "is_staff": user.is_staff if user else False,
        "SOCIALACCOUNT_ENABLED": settings.SOCIALACCOUNT_ENABLED,
        "SOCIALACCOUNT_ONLY": settings.SOCIALACCOUNT_ONLY,
    }
