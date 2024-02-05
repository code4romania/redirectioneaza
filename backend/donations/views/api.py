import json
import logging
from datetime import date

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.files import File
from django.core.management import call_command
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from redirectioneaza.common.messaging import send_email
from .base import AccountHandler, BaseHandler
from ..models.jobs import Job, JobStatusChoices
from ..models.main import Ngo
from ..pdf import create_pdf

logger = logging.getLogger(__name__)


class CheckNgoUrl(AccountHandler):
    def get(self, request, ngo_url, *args, **kwargs):
        # if we don't receive an ngo url or it's not a logged in user or not and admin
        if not ngo_url or not request.user and not request.user.is_staff:
            raise PermissionDenied()

        if not Ngo.objects.filter(slug=ngo_url).count():
            return HttpResponse()
        else:
            raise BadRequest()


class NgosApi(BaseHandler):
    def get(self, request, *args, **kwargs):
        # get all the visible ngos
        ngos = Ngo.objects.filter(is_active=True).all()

        response = []
        for ngo in ngos:
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

        # if we have an form created for this ngo, return the url
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
        ngo.prefilled_form.save(filename, File(pdf))

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
            call_command("download_donations", new_job.id, "--run")
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
            ngo = Ngo.objects.create()
            ngo.save()
            request.user.ngo = ngo
            request.user.save()

        ngo.logo = logo_file
        ngo.save()

        return JsonResponse({"file_urls": [ngo.logo.url]})


class Webhook(BaseHandler):
    def post(self, request, *args, **kwargs):
        body = json.decode(request.body)

        data = body.get("data", {})
        job_id = body.get("jobId")
        error = body.get("error")
        url = body.get("url")

        if not job_id:
            logger.error("Did not receive jobId argument")
            raise BadRequest()

        # mark the job as done
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            logger.error("Received an webhook. Could not find job with id {}".format(data.get("jobId")))
            raise BadRequest()

        if job.status == "done":
            logger.warning("Job with id {} is already done. Duplicate webhook".format(job.id))

        if url:
            job.url = url
            job.status = "done"
        elif error:
            job.status = "error"

        job.save()

        send_email(
            subject=_("Exportul de formulare este gata"),
            to_emails=[job.owner.email],
            text_template="emails/zipped_forms/zipped_forms.txt",
            html_template="emails/zipped_forms/zipped_forms.html",
            context={"link": url},
        )
