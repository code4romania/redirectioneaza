import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from donations.models.byof import OwnFormsUpload
from donations.models.donors import Donor
from donations.models.jobs import Job
from donations.models.ngos import Cause, Ngo

logger = logging.getLogger(__name__)


def reset_staging(generate_orgs_count=0, generate_causes_count=0, generate_donations_count=0):
    if settings.ENVIRONMENT not in ("staging", "development"):
        logger.warning(
            "Cannot reset the staging environment because the current environment is %s", settings.ENVIRONMENT
        )
        return

    # Delete all "bring your own forms"
    for upload in OwnFormsUpload.objects.all():
        upload.uploaded_data.delete(save=False)
    logger.info("Deleted all bring your own form PDFs")

    OwnFormsUpload.objects.all().delete()
    logger.info("Deleted all bring your own forms")

    # Delete all donations download jobs
    for job in Job.objects.all():
        job.zip.delete(save=False)
    logger.info("Deleted all download jobs zips")

    Job.objects.all().delete()
    logger.info("Deleted all download jobs")

    # Delete all donations
    for donor in Donor.objects.all():
        donor.pdf_file.delete(save=False)
    logger.info("Deleted all redirection form PDFs")

    Donor.objects.all().delete()
    logger.info("Deleted all redirection forms")

    # Delete all causes
    for cause in Cause.objects.all():
        cause.prefilled_form.delete(save=False)
    logger.info("Deleted all cause prefilled form PDFs")

    Cause.objects.all().delete()
    logger.info("Deleted all causes")

    # Delete all NGOs
    Ngo.objects.all().delete()
    logger.info("Deleted all NGOs")

    # Delete all users except the default admin accounts
    get_user_model().objects.exclude(email__in=(settings.DJANGO_ADMIN_EMAIL, settings.SEED_ADMIN_EMAIL)).delete()

    # TODO: Add logic to generate new organizations, causes and donations if the counts are greater than 0


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
