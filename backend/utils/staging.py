import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_q.tasks import async_task

logger = logging.getLogger(__name__)


def reset_staging(generate_orgs_count=0, generate_causes_count=0, generate_donations_count=0):
    if settings.ENVIRONMENT not in ("staging", "development"):
        logger.warning(
            "Cannot reset the staging environment because the current environment is %s", settings.ENVIRONMENT
        )
        return

    pass


def schedule_reset_staging(request):
    if not request.user or not request.user.has_perm("can_reset_staging"):
        raise PermissionDenied

    logger.info("Scheduling a staging environment reset")
    async_task(reset_staging, generate_orgs_count=100, generate_causes_count=100, generate_donations_count=1000)

    messages.add_message(
        request,
        messages.SUCCESS,
        _("The staging environment reset has been scheduled. This may take a few minutes."),
    )
    return redirect(reverse("admin:index"))
