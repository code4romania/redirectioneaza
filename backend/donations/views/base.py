from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView


class BaseTemplateView(TemplateView):
    user_model = get_user_model()

    def _get_checked_property(self, property_name: str, default_value: str) -> Any:
        is_production: bool = settings.ENVIRONMENT == "development"

        if not hasattr(self, property_name) and not is_production:
            raise AttributeError(f"Property '{property_name}' is missing in '{self.__class__.__name__}'.")

        if not (property_value := getattr(self, property_name)) and not is_production:
            raise ValueError(f"Property '{property_name}' in '{self.__class__.__name__}' is empty.")

        return property_value or default_value

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


class BaseVisibleTemplateView(BaseTemplateView):
    user_model = get_user_model()
    title: str = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = self._get_checked_property("title", "redirectioneaza.ro")

        return context
