import logging
from datetime import date
from typing import Dict, List

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.files import File
from django.core.management import call_command
from django.db.models import Q, QuerySet
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from redirectioneaza.common.cache import cache_decorator

from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import ALL_NGOS_CACHE_KEY, Ngo
from ..pdf import create_pdf
from ..workers.update_organization import update_organization
from .base import BaseTemplateView

logger = logging.getLogger(__name__)


def get_ngo_response_item(ngo) -> Dict:
    return {
        "name": ngo.name,
        "url": reverse("twopercent", kwargs={"ngo_url": ngo.slug}),
        "logo": ngo.logo.url if ngo.logo else None,
        "active_region": ngo.active_region,
        "description": ngo.description,
    }


class UpdateFromNgohub(BaseTemplateView):
    def post(self, request, *args, **kwargs):
        redirect_success = redirect(reverse("organization"))
        redirect_error = redirect(reverse("organization"))

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
    def validate_ngo_slug(cls, user, slug):
        if not slug or not user and not user.is_staff:
            raise PermissionDenied()

        if slug.lower() in cls.ngo_url_block_list:
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


class SearchNgosApi(TemplateView):
    def _configure_search_query(self, query: str, language_code: str) -> SearchQuery:
        if language_code == "ro":
            return SearchQuery(query, config="romanian_unaccent")

        return SearchQuery(query)

    def _configure_search_vector(self, language_code: str) -> SearchVector:
        if language_code == "ro":
            return SearchVector("name", weight="A", config="romanian_unaccent")

        return SearchVector("name", weight="A")

    def get(self, request, *args, **kwargs):
        query = request.GET.get("q", "")

        if not query:
            return JsonResponse([], safe=False)

        language_code: str = settings.LANGUAGE_CODE
        if hasattr(self.request, "LANGUAGE_CODE") and self.request.LANGUAGE_CODE:
            language_code = self.request.LANGUAGE_CODE
        language_code = language_code.lower()

        search_vector: SearchVector = self._configure_search_vector(language_code)
        search_query: SearchQuery = self._configure_search_query(query, language_code)

        ngos: QuerySet[Ngo] = (
            Ngo.active.annotate(
                rank=SearchRank(search_vector, search_query),
                similarity=TrigramSimilarity("name", query),
            )
            .filter(Q(rank__gte=0.3) | Q(similarity__gt=0.3))
            .order_by("name")
            .distinct("name")
        )

        response: List[Dict] = []
        for ngo in ngos:
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

        # else, create a new one and save it for future use
        ngo_dict = {
            "name": ngo.name,
            "cif": ngo.registration_number,
            "account": ngo.bank_account.upper(),
            # do not add any checkmark on this form regarding the number of years
            "years_checkmark": False,
            # "two_years": False,
            "is_social_service_viable": ngo.is_social_service_viable,
        }
        donor = {
            # we assume that ngos are looking for people with income from wages
            "income": "wage"
        }
        pdf = create_pdf(donor, ngo_dict)

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


class GetNgoForms(BaseTemplateView):
    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("login"))

        ngo = request.user.ngo
        if not ngo:
            return redirect(reverse("contul-meu"))

        if not ngo.is_active:
            return redirect(reverse("contul-meu"))

        try:
            latest_job: Job = Job.objects.filter(ngo=ngo).latest("date_created")

            form_retry_threshold = timezone.now() - timezone.timedelta(
                minutes=settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES
            )
            if latest_job.status != JobStatusChoices.ERROR and latest_job.date_created > form_retry_threshold:
                return redirect(reverse("contul-meu"))

        except Job.DoesNotExist:
            pass

        DONATION_LIMIT = date(
            year=settings.DONATIONS_LIMIT_YEAR,
            month=settings.DONATIONS_LIMIT_MONTH,
            day=settings.DONATIONS_LIMIT_DAY,
        )

        if timezone.now().date() > DONATION_LIMIT + timezone.timedelta(
            days=settings.TIMEDELTA_DONATIONS_LIMIT_DOWNLOAD_DAYS
        ):
            return redirect(reverse("contul-meu"))

        new_job: Job = Job(ngo=ngo, owner=request.user)
        new_job.save()

        try:
            call_command("download_donations", new_job.id)
        except Exception as e:
            logging.error(e)
            new_job.status = JobStatusChoices.ERROR
            new_job.save()

        return redirect(reverse("contul-meu"))


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
