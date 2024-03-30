from django.contrib.auth import get_user_model
from django.views.generic import TemplateView


class BaseAccountView(TemplateView):
    user_model = get_user_model()
