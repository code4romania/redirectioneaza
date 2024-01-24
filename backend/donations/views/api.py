from django.conf import settings
from django.core.exceptions import PermissionDenied, BadRequest
from django.http import HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from ..models import Ngo
from .base import BaseHandler, AccountHandler


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


@method_decorator(csrf_exempt, name="dispatch")
class GetUploadUrl(AccountHandler):
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("GetUploadUrl not implemented yet")

    def post(self, request, *args, **kwargs):
        # logo_file = request.FILES.get("files")
        # print(logo_file)
        raise NotImplementedError("GetUploadUrl not implemented yet")


class Webhook(BaseHandler):
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("Webhook not implemented yet")
