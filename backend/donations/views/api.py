import json
import logging

from urllib.request import Request, urlopen
from datetime import datetime, date

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, BadRequest
from django.core.files import File
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone

from ..models.main import Ngo, Donor, ngo_directory_path, hash_id_secret
from ..models.jobs import Job, JobStatusChoices
from ..pdf import create_pdf
from .base import BaseHandler, AccountHandler


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
                    "logo": ngo.logo if ngo.logo else settings.DEFAULT_NGO_LOGO,
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

        now = timezone.now()
        start_of_year = datetime(now.year, 1, 1, 0, 0)

        if now.date() > DONATION_LIMIT:
            return redirect(reverse("contul-meu"))

        # get all the forms that have been completed since the start of the year
        # and they are also signed
        donations = Donor.objects.filter(ngo=ngo, date_created__gte=start_of_year, has_signed=True).all()

        # extract only the urls from the array of models
        urls = [u.pdf_file.url if u.pdf_file else u.pdf_url for u in donations if u.has_signed]

        # if no forms
        if len(urls) == 0:
            logging.warn("Could not find any signed forms for this ngo: {}".format(ngo.id))
            return redirect(reverse("contul-meu"))

        # create job
        job = Job(
            ngo=ngo,
            owner=request.user,
        )
        job.save()

        export_destination = ngo_directory_path(
            "exports", ngo, "export_{}_{}.zip".format(job.id, hash_id_secret(timezone.now(), job.id))
        )

        # make request
        params = {
            "passphrase": settings.ZIP_SECRET,
            "urls": urls,
            "path": export_destination,
            "webhook": {
                "url": "https://{}{}".format(settings.APEX_DOMAIN, reverse("webhook")),
                "data": {"jobId": job.id},
            },
        }

        request = Request(url=settings.ZIP_ENDPOINT, data=params, headers={"Content-type": "application/json"})

        try:
            httpresp = urlopen(request)
            response = json.decode(httpresp.read())
            logging.info(response)
            httpresp.close()
        except Exception as e:
            logging.exception(e)
            # if job failed to start remotely
            job.status = JobStatusChoices.ERROR
            job.save()
        finally:
            return redirect(reverse("contul-meu"))


@method_decorator(login_required(login_url=reverse_lazy("login")), name="dispatch")
class GetUploadUrl(AccountHandler):
    def post(self, request, *args, **kwargs):
        files = request.FILES
        if len(files) != 1:
            raise BadRequest()

        ngo = request.user.ngo
        if not ngo:
            raise BadRequest()
            # # TODO: should we create the NGO here?
            # ngo = Ngo.objects.create()
            # ngo.save()
            # request.user.ngo = ngo
            # request.user.save()

        ngo.logo = files[0]
        ngo.save()

        self.return_json({"file_urls": [ngo.logo.url]})


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

        # TODO:
        # send email
        # self.send_dynamic_email(
        #     template_id="d-312ab0a4221944e3ac728ae08c504a7c", email=job.owner.email, data={"link": url}
        # )
