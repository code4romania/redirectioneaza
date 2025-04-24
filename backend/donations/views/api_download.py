import csv
import io
import logging
from typing import Dict, List
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.core.files.base import ContentFile
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from donations.models import Donor, Ngo, RedirectionsDownloadJob
from donations.models.common import JobStatusChoices
from donations.views.base import BaseTemplateView
from donations.views.ngo_account_filters import get_active_filters, get_queryset_filters, get_redirections_filters
from redirectioneaza.common.messaging import extend_email_context, send_email


logger = logging.getLogger(__name__)


def fill_redirections_csv(csv_writer: csv.writer, redirections_queryset: QuerySet[Donor]):
    redirections_queryset = redirections_queryset.prefetch_related("cause").only(
        "f_name",
        "l_name",
        "email",
        "phone",
        "is_anonymous",
        "two_years",
        "city",
        "county",
        "date_created",
        "has_signed",
        "cause__bank_account",
    )

    csv_writer.writerow(
        [
            _("Name"),
            _("Email"),
            _("Phone"),
            _("Period (years)"),
            _("IBAN"),
            _("Has Signed"),
            _("Locality"),
            _("County"),
            _("Redirection Date"),
        ]
    )

    redirection: Donor
    for redirection in redirections_queryset:
        full_name = f"{redirection.f_name} {redirection.l_name}"
        email = redirection.email if not redirection.is_anonymous else _("anonymous")
        phone = redirection.phone if not redirection.is_anonymous else _("anonymous")
        period = "2" if redirection.two_years else "1"
        iban = redirection.cause.bank_account if redirection.cause else _("N/A")
        has_signed = "Yes" if redirection.has_signed else "No"
        locality = redirection.city
        county = redirection.county
        redirection_date = redirection.date_created.strftime("%Y-%m-%d %H:%M")

        csv_writer.writerow(
            [
                full_name,
                email,
                phone,
                period,
                iban,
                has_signed,
                locality,
                county,
                redirection_date,
            ]
        )


def generate_csv_from_download_job(download_job_id: int):
    try:
        download_job: RedirectionsDownloadJob = RedirectionsDownloadJob.objects.get(pk=download_job_id)
    except RedirectionsDownloadJob.DoesNotExist:
        error_message = f"Download job with ID {download_job_id} does not exist."
        logger.error(error_message)
        return {"error": error_message}

    try:
        csv_filters: List[Dict] = download_job.queryset
        qs_filters = {csv_filter["qs_key"]: csv_filter["qs_value"] for csv_filter in csv_filters}

        filters_suffix = "_".join([f"{quote(str(key))}:{quote(str(value))}" for key, value in qs_filters.items()])
        filename = f"redirect-n_{download_job.ngo.pk:04d}-{filters_suffix}.csv"

        ngo: Ngo = Ngo.objects.get(pk=download_job.ngo.pk)
        redirections_queryset: QuerySet[Donor] = ngo.donor_set.filter(**qs_filters).order_by("-date_created")

        with io.StringIO() as csv_buffer:
            csv_writer = csv.writer(csv_buffer)
            fill_redirections_csv(csv_writer=csv_writer, redirections_queryset=redirections_queryset)

            binary_buffer = io.BytesIO(csv_buffer.getvalue().encode("utf-8"))
            csv_content = ContentFile(binary_buffer.getvalue())

            download_job.output_file.save(filename, csv_content, save=False)

        download_job.output_rows = redirections_queryset.count()
        download_job.status = JobStatusChoices.DONE
        download_job.save()
    except Exception as e:
        error_message = f"Error generating CSV file: {e}"
        logger.error(error_message)
        download_job.status = JobStatusChoices.ERROR
        download_job.save()
        return {"error": error_message}

    mail_context = {
        "date_generated": timezone.now().strftime("%Y-%m-%d %H:%M"),
        "action_url": reverse("my-organization:redirections-download-link", kwargs={"job_id": download_job.pk}),
        "filters": {csv_filter["title"]: csv_filter["value"] for csv_filter in csv_filters},
    }
    mail_context.update(extend_email_context())

    send_email(
        subject=_("Redirections CSV file"),
        to_emails=[ngo.email],
        text_template="emails/ngo/download-csv/main.txt",
        html_template="emails/ngo/download-csv/main.html",
        context=mail_context,
    )

    return {"success": True, "file_url": download_job.output_file.url}


class DownloadNgoRedirections(BaseTemplateView):
    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        ngo: Ngo = request.user.ngo if request.user.ngo else None

        if not ngo or not ngo.can_receive_redirections:
            messages.error(request, _("Your organization can not receive forms currently."))
            return redirect(reverse_lazy("my-organization:presentation"))

        redirections_filters = get_redirections_filters(ngo)
        queryset_filters = get_queryset_filters(filters=redirections_filters, request_params=request.POST)
        redirections_queryset: QuerySet[Donor] = ngo.donor_set.filter(**queryset_filters)

        queryset_size = redirections_queryset.count()
        if queryset_size == 0:
            error_message = _("There are no redirections available for download.")
            return HttpResponseBadRequest(error_message)

        csv_filters = self.build_job_filters(redirections_filters, request)

        try:
            download_job = RedirectionsDownloadJob.objects.create(ngo=ngo, queryset=csv_filters)
        except TypeError as e:
            logger.error(f"Error creating download job: {e}")
            return HttpResponseBadRequest(
                _("An error occurred while attempting to download the forms. Adjusting the filters might help.")
            )

        if settings.DONATIONS_CSV_DOWNLOAD_METHOD == "async":
            async_task(generate_csv_from_download_job, download_job.pk)
            return HttpResponse(
                content=_("The CSV file is being generated and will be sent to your email shortly."),
                status=202,
            )

        try:
            output = generate_csv_from_download_job(download_job.pk)
            if "error" in output:
                return HttpResponseBadRequest(output["error"])
            elif "file_url" in output:
                response = HttpResponse(
                    content_type="text/csv",
                    content=output["file_url"],
                )
                response["Content-Disposition"] = f'attachment; filename="{download_job.output_file.name}"'

                return response
        except Exception as e:
            logger.error(f"Error generating CSV file: {e}")
            return HttpResponseBadRequest(_("An error occurred while generating the CSV file."))

        error_message = _("An unknown error occurred while generating the CSV file.")
        logger.error(error_message)
        return HttpResponseBadRequest(error_message)

    def build_job_filters(self, redirections_filters, request):
        csv_filters = []
        for active_filter in get_active_filters(filters=redirections_filters, request_params=request.POST):
            csv_filters.append(
                {
                    "qs_key": active_filter["filter"].queryset_key,
                    "title": str(active_filter["filter"].title),
                    "value": active_filter["value"],
                    "value_title": active_filter["value_title"],
                    "qs_value": active_filter["filter"].transform_to_qs_value(active_filter["value"]),
                }
            )
        return csv_filters
