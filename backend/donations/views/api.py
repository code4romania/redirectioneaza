from django.shortcuts import render
from django.conf import settings

from .base import BaseHandler, AccountHandler


class CheckNgoUrl(AccountHandler):
    pass


class NgosApi(BaseHandler):
    pass


class GetNgoForm(BaseHandler):
    pass


class GetNgoForms(AccountHandler):
    pass


class GetUploadUrl(AccountHandler):
    pass


class Webhook(BaseHandler):
    pass
