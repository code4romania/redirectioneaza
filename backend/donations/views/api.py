import logging
import random
import string
from datetime import date

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.files import File
from django.core.management import call_command
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from redirectioneaza.common.cache import cache_decorator
from .base import AccountHandler, BaseHandler
from ..models.jobs import Job, JobStatusChoices
from ..models.main import ALL_NGOS_CACHE_KEY, Ngo
from ..pdf import create_pdf

logger = logging.getLogger(__name__)


class CheckNgoUrl(AccountHandler):
    block_list = (
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
        "password",
        "pentru-ong-uri",
        "politica",
        "static",
        "termeni",
        "verify",
    )

    def get(self, request, ngo_url, *args, **kwargs):
        # if we don't receive an NGO url, or it's not a logged-in user or not and admin
        if not ngo_url or not request.user and not request.user.is_staff:
            raise PermissionDenied()

        if ngo_url.lower() in self.block_list:
            return HttpResponseBadRequest()

        if Ngo.objects.filter(slug=ngo_url.lower()).count():
            return HttpResponseBadRequest()

        return HttpResponse()


class NgosApi(BaseHandler):
    @staticmethod
    @cache_decorator(cache_key_prefix=ALL_NGOS_CACHE_KEY, timeout=settings.CACHE_TIMEOUT_SMALL)
    def _get_all_ngos() -> list:
        return Ngo.active.order_by("name")

    def get(self, request, *args, **kwargs):
        # get all the visible ngos
        ngos = self._get_all_ngos()

        response = []
        for ngo in ngos:
            if not ngo.slug:
                continue

            response.append(
                {
                    "name": ngo.name,
                    "url": reverse("twopercent", kwargs={"ngo_url": ngo.slug}),
                    "logo": ngo.logo.url if ngo.logo else settings.DEFAULT_NGO_LOGO,
                    "active_region": ngo.active_region,
                    "description": ngo.description,
                }
            )

        return JsonResponse(response, safe=False)


class GetNgoForm(BaseHandler):
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
            "special_status": ngo.has_special_status,
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

        ngo.form_url = ngo.prefilled_form.url
        ngo.save()

        return redirect(ngo.prefilled_form.url)


class GetNgoForms(AccountHandler):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("login"))

        ngo = request.user.ngo
        if not ngo:
            return redirect(reverse("contul-meu"))

        DONATION_LIMIT = date(timezone.now().year, 5, 25)

        if timezone.now().date() > DONATION_LIMIT:
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
class GetUploadUrl(AccountHandler):
    def post(self, request, *args, **kwargs):
        logo_file = request.FILES.get("files")
        if not logo_file:
            raise BadRequest()

        ngo = request.user.ngo
        if not ngo:
            ngo = Ngo()
            ngo.slug = "".join(random.choices(string.ascii_lowercase + "-", k=8))
            ngo.save()
            request.user.ngo = ngo
            request.user.save()

        ngo.logo = logo_file
        ngo.save()

        return JsonResponse({"file_urls": [ngo.logo.url]})
