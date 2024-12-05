from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import messages
from django.template.loader import render_to_string
from django.conf import settings

from .admin_dashboard import callback as admin_callback

UserModel = get_user_model()


def callback(request, context):
    user: UserModel = request.user

    messages.warning(
        request,
        render_to_string(
            "admin/announcements/work_in_progress.html",
            context={
                "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            },
        ),
    )

    if not user or not user.is_authenticated:
        return context

    if user.is_admin:
        return admin_callback(request, context)

    return {"redirect": reverse("contul-meu")}
