import logging
from typing import Dict, List

from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.core.files import File
from django.core.management import call_command
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from .base import BaseTemplateView
from .common import (
    NgoCauseMixedSearchMixin,
    get_cause_response_item,
    get_is_over_donation_archival_limit,
    get_was_last_job_recent,
)
from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import Cause, Ngo
from ..pdf import create_ngo_pdf
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
        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            raise Http404()

        # if we have a form created for this ngo, return the url
        if ngo.prefilled_form:
            return redirect(ngo.prefilled_form.url)

        pdf = create_ngo_pdf(ngo)

        # filename = "Formular 2% - {0}.pdf".format(ngo.name)
        filename = "Formular_donatie.pdf"
        try:
            ngo.prefilled_form.save(filename, File(pdf))
        except AttributeError:
            # if the form file didn't reach the storage yet, redirect the user back to the download page
            pdf.close()
            return redirect(reverse("api-ngo-form-url", kwargs={"ngo_url": ngo_url}))

        # close the file after it has been uploaded
        pdf.close()

        return redirect(ngo.prefilled_form.url)


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

        new_job: Job = Job(ngo=ngo, owner=request.user)
        new_job.save()

        try:
            call_command("download_donations", new_job.id)
        except Exception as e:
            logging.error(e)

            new_job.status = JobStatusChoices.ERROR
            new_job.save()

        return redirect(success_redirect_url)


@method_decorator(login_required(login_url=reverse_lazy("login")), name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class GetUploadUrl(BaseTemplateView):
    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        logo_file = request.FILES.get("files")
        if not logo_file:
            logger.warning("No logo file uploaded for the NGO logo upload")
            raise BadRequest

        ngo = request.user.ngo
        if not ngo:
            logger.warning("No NGO selected for the NGO logo upload")
            raise BadRequest

        ngo.logo = logo_file
        ngo.save()

        return JsonResponse({"file_urls": [ngo.logo.url]})
