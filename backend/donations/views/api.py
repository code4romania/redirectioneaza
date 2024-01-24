import json

import logging
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied, BadRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator

from ..models import Ngo
from ..models.jobs import Job
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
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("GetNgoForm not implemented yet")


class GetNgoForms(AccountHandler):
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("GetNgoForms not implemented yet")


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
