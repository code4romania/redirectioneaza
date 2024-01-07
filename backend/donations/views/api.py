from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .base import BaseHandler, AccountHandler


class CheckNgoUrl(AccountHandler):
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("CheckNgoUrl not implemented yet")


class NgosApi(BaseHandler):
    template_name = "all-ngos.html"


class GetNgoForm(BaseHandler):
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("GetNgoForm not implemented yet")


class GetNgoForms(AccountHandler):
    def get(self, request, *args, **kwargs):
        raise NotImplementedError("GetNgoForms not implemented yet")


@method_decorator(csrf_exempt, name='dispatch')
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
