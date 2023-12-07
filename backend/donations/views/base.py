from django.views.generic import TemplateView


class Handler(TemplateView):
    pass


class BaseHandler(Handler):
    pass


class AccountHandler(BaseHandler):
    pass
