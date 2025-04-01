import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.files import File
from django.core.management import call_command
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import NGO_CAUSES_QUERY_CACHE_KEY, Cause, Ngo
from ..pdf import create_cause_pdf
from ..workers.update_organization import update_organization
from .base import BaseTemplateView
from .common.misc import (
    get_cause_response_item,
    get_ngo_cause,
    has_archive_generation_deadline_passed,
    has_recent_archive_job,
)
from .common.search import NgoCauseMixedSearchMixin

logger = logging.getLogger(__name__)

UserModel = get_user_model()


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
    queryset = Cause.public_active

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


class GenerateCauseArchive(BaseTemplateView):
    def generate_archive_for_cause_slug(self, cause_slug: Optional[str], request) -> Optional[Job]:
        if not cause_slug:
            return None

        ngo: Ngo = request.user.ngo
        if not ngo or not ngo.can_receive_forms:
            return None

        try:
            cause = ngo.causes.get(slug=cause_slug)
        except Cause.DoesNotExist:
            return None

        if has_recent_archive_job(cause):
            return None

        if has_archive_generation_deadline_passed():
            return None

        new_job: Job = Job(ngo=ngo, cause=cause, owner=request.user)
        new_job.save()

        try:
            if settings.FORMS_DOWNLOAD_METHOD == "async":
                call_command("download_donations", new_job.id)
            else:
                call_command("download_donations", new_job.id, "--run")
        except Exception as e:
            logging.error(e)

            new_job.status = JobStatusChoices.ERROR
            new_job.save()

        # noinspection StrFormat
        cache.delete(NGO_CAUSES_QUERY_CACHE_KEY.format(ngo.pk))

        return new_job

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        success_redirect_url = reverse("my-organization:archives")

        failure_redirect_url = reverse("my-organization:redirections")
        failure_response = redirect(failure_redirect_url)

        post_data = request.POST
        cause_slug: str = post_data.get("cause_slug")

        status = self.generate_archive_for_cause_slug(cause_slug, request)
        if not status:
            return failure_response

        return redirect(success_redirect_url)
