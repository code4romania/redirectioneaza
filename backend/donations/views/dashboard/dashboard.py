from django.contrib.auth import get_user_model
from django.urls import reverse

from .admin_dashboard import callback as admin_callback

UserModel = get_user_model()


def callback(request, context):
    user: UserModel = request.user

    if not user or not user.is_authenticated:
        return context

    if user.is_admin:
        return admin_callback(request, context)

    return {"redirect": reverse("my-organization:dashboard")}
