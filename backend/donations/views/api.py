from .base import BaseHandler, AccountHandler


class CheckNgoUrl(AccountHandler):
    pass


class NgosApi(BaseHandler):
    template_name = "all-ngos.html"


class GetNgoForm(BaseHandler):
    pass


class GetNgoForms(AccountHandler):
    pass


class GetUploadUrl(AccountHandler):
    pass


class Webhook(BaseHandler):
    pass
