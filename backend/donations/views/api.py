import logging
from typing import Dict, List

from django.core.files import File
from django.core.management import call_command
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from .base import BaseTemplateView
from .common import (
    NgoCauseMixedSearchMixin,
    get_cause_response_item,
    get_is_over_donation_archival_limit,
    get_ngo_cause,
    get_was_last_job_recent,
)
from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import Cause, Ngo
from ..pdf import create_cause_pdf
from ..workers.update_organization import update_organization

logger = logging.getLogger(__name__)


class UpdateFromNgohub(BaseTemplateView):
    def post(self, request, *args, **kwargs):
        redirect_success = redirect(reverse("my-organization:dashboard"))
        redirect_error = redirect(reverse("home"))

        user = request.user

        if not user.ngo or not user.ngo.is_active:
            return redirect_error

        update_organization(user.ngo.pk)

        return redirect_success


class SearchCausesApi(TemplateView, NgoCauseMixedSearchMixin):
    queryset = Cause.active

    def get(self, request, *args, **kwargs):
        causes = self.search()

        response: List[Dict] = []
        for cause in causes:
            if not cause.slug:
                continue

            response.append(get_cause_response_item(cause))

        return JsonResponse(response, safe=False)


class GetNgoForm(TemplateView):
    def get(self, request, ngo_url, *args, **kwargs):
        cause, ngo = get_ngo_cause(ngo_url)

        # if we have a form created for this ngo, return the url
        if cause.prefilled_form:
            return redirect(cause.prefilled_form.url)

        pdf = create_cause_pdf(cause, ngo)

        # filename = "Formular 2% - {0}.pdf".format(ngo.name)
        filename = "formular_donatie.pdf"
        try:
            cause.prefilled_form.save(filename, File(pdf))
        except AttributeError:
            # if the form file didn't reach the storage yet, redirect the user back to the download page
            pdf.close()
            return redirect(reverse("api-ngo-form-url", kwargs={"ngo_url": ngo_url}))

        # close the file after it has been uploaded
        pdf.close()

        return redirect(cause.prefilled_form.url)


class DownloadNgoForms(BaseTemplateView):
    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("login"))

        failure_redirect_url = reverse("my-organization:redirections")
        success_redirect_url = reverse("my-organization:archives")

        ngo: Ngo = request.user.ngo
        if not ngo:
            return redirect(failure_redirect_url)

        if not ngo.is_active:
            return redirect(failure_redirect_url)

        last_job_was_recent = get_was_last_job_recent(ngo)
        if last_job_was_recent:
            return redirect(failure_redirect_url)

        if get_is_over_donation_archival_limit():
            return redirect(failure_redirect_url)

        cause: Cause = ngo.causes.first()
        new_job: Job = Job(ngo=ngo, cause=cause, owner=request.user)
        new_job.save()

        try:
            call_command("download_donations", new_job.id)
        except Exception as e:
            logging.error(e)

            new_job.status = JobStatusChoices.ERROR
            new_job.save()

        return redirect(success_redirect_url)
