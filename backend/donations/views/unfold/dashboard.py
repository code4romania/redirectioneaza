from donations.views.unfold.admin_dashboard import admin_callback
from donations.views.unfold.ngo_dashboard import ngo_callback


def callback(request, context):
    user = request.user

    if not user or not user.is_authenticated:
        return context

    if user.is_superuser:
        return admin_callback(request, context)

    return ngo_callback(request, context)
