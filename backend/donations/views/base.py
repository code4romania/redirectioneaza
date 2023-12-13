from django.contrib.auth import get_user_model
from django.views.generic import TemplateView


class Handler(TemplateView):
    pass


class BaseHandler(Handler):
    pass


class AccountHandler(BaseHandler):
    user_model = get_user_model()
