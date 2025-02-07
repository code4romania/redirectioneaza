import logging
from typing import Dict, List

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.files import File
from django.core.management import call_command
from django.db.models import QuerySet
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from redirectioneaza.common.cache import cache_decorator

from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import ALL_NGOS_CACHE_KEY, Ngo, ngo_slug_validator
from ..pdf import create_ngo_pdf
from ..workers.update_organization import update_organization
from .base import BaseTemplateView
from .common import NgoSearchMixin, get_is_over_donation_archival_limit, get_ngo_response_item, get_was_last_job_recent

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


class CheckNgoUrl(BaseTemplateView):
    ngo_url_block_list = (
        "",
        "admin",
        "api",
        "asociatia",
        "asociatii",
        "cont-nou",
        "contul-meu",
        "cron",
        "date-cont",
        "despre",
        "donatie",
        "download",
        "forgot",
        "health",
        "login",
        "logout",
        "media",
        "ngos",
        "nota-de-informare",
        "ong",
        "organizatie",
        "organizatii",
        "organizatia",
        "password",
        "pentru-ong-uri",
        "politica",
        "static",
        "termeni",
        "verify",
    )

    def get(self, request, ngo_url, *args, **kwargs):
        return self.validate_ngo_slug(request.user, ngo_url)

    @classmethod
    def check_slug_is_blocked(cls, slug):
        if slug.lower() in cls.ngo_url_block_list:
            return True

        return False

    @classmethod
    def check_slug_is_reused(cls, slug, user):
        ngo_queryset: QuerySet[Ngo] = Ngo.objects

        try:
            if user.ngo:
                ngo_queryset = ngo_queryset.exclude(id=user.ngo.id)
        except AttributeError:
            # Anonymous users don't have the .ngo attribute
            pass

        if ngo_queryset.filter(slug=slug.lower()).count():
            return True

        return False

    @classmethod
    def validate_ngo_slug(cls, user, slug):
        if not slug or not user and not user.is_staff:
            raise PermissionDenied()

        if user.is_anonymous:
            raise PermissionDenied()

        if ngo_slug_validator(slug) in cls.ngo_url_block_list:
            return HttpResponseBadRequest()

        ngo_queryset = Ngo.objects

        try:
            if user.ngo:
                ngo_queryset = ngo_queryset.exclude(id=user.ngo.id)
        except AttributeError:
            # Anonymous users don't have the .ngo attribute
            pass

        if ngo_queryset.filter(slug=slug.lower()).count():
            return HttpResponseBadRequest()

        return HttpResponse()


class NgosApi(TemplateView):
    @staticmethod
    @cache_decorator(timeout=settings.TIMEOUT_CACHE_NORMAL, cache_key=ALL_NGOS_CACHE_KEY)
    def _get_all_ngos() -> list:
        return Ngo.active.order_by("name")

    def get(self, request, *args, **kwargs):
        # get all the visible ngos
        ngos = self._get_all_ngos()

        response = []
        for ngo in ngos:
            if not ngo.slug:
                continue

            response.append(get_ngo_response_item(ngo))

        return JsonResponse(response, safe=False)


class SearchNgosApi(TemplateView, NgoSearchMixin):
    queryset = Ngo.active

    def get(self, request, *args, **kwargs):

        ngos_queryset = self.search()

        response: List[Dict] = []
        for ngo in ngos_queryset:
            if not ngo.slug:
                continue

            response.append(get_ngo_response_item(ngo))

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
