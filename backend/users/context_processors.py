from django.http import HttpRequest


def is_admin(request: HttpRequest):
    return {
        "is_admin": request.user.is_superuser,
    }
