from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from donations.common.validation.registration_number import ngo_id_number_validator
from donations.models.ngos import Cause, Ngo
from donations.views.base import BaseContextPropertiesMixin, BaseVisibleTemplateView
from users.models import User


class NgoBaseView(BaseContextPropertiesMixin):
    title = _("Organization details")
    sidebar_item_target = None
    request: HttpRequest

    def get_extra_context(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        return {
            "user": user,
            "ngo": ngo,
            "title": self._get_checked_property("title", ""),
            "active_item": self._get_checked_property("sidebar_item_target", ""),
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }


class NgoBaseTemplateView(NgoBaseView, BaseVisibleTemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_extra_context())

        return context

    def get_missing_fields(
        self,
        *,
        source: str,
        ngo: Optional[Ngo],
        cause: Optional[Cause],
    ) -> Optional[Dict[str, str]]:
        """
        Returns a dictionary with the missing fields for the organization or the cause.
        If there are no missing fields, it returns None.
        """

        if missing_ngo_fields := self.get_missing_ngo_fields(ngo):
            return {
                "type": "ngo",
                "fields": missing_ngo_fields,
                "cta_message": _("Go to the organization details.") if source == "cause" else "",
                "cta_url": reverse_lazy("my-organization:presentation") if source == "cause" else "",
            }
        elif missing_cause_fields := self.get_cause_missing_fields(cause):
            return {
                "type": "cause",
                "fields": missing_cause_fields,
                "cta_message": _("Go to the form.") if source == "ngo" else "",
                "cta_url": reverse_lazy("my-organization:form") if source == "ngo" else "",
            }

        return None

    def get_cause_missing_fields(self, cause: Optional[Cause]) -> Optional[List[str]]:
        if not cause:
            missing_fields = Cause.mandatory_fields_names_capitalized()
        else:
            missing_fields = cause.missing_mandatory_fields_names_capitalized()

        return missing_fields

    def get_missing_ngo_fields(self, ngo: Optional[Ngo]) -> Optional[List[str]]:
        if not ngo:
            missing_fields = Ngo.mandatory_fields_names_capitalized()
        else:
            missing_fields = ngo.missing_mandatory_fields_names_capitalize

        return missing_fields

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_superuser:
            return redirect(reverse("admin:index"))

        return super().get(request, *args, **kwargs)


class NgoBaseListView(NgoBaseView, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_extra_context())

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


def validate_iban(bank_account) -> Optional[str]:
    if not bank_account:
        return None

    if len(bank_account) != 24:
        return _("The IBAN number must have 24 characters")

    if not bank_account.isalnum():
        return _("The IBAN number must contain only letters and digits")

    if not bank_account.startswith("RO"):
        return _("The IBAN number must start with 'RO'")

    return None


def validate_registration_number(ngo, registration_number) -> Optional[str]:
    try:
        ngo_id_number_validator(registration_number)
    except ValidationError:
        return f'CIF "{registration_number}" pare incorect'

    reg_num_query: QuerySet[Ngo] = Ngo.objects.filter(registration_number=registration_number)
    if ngo.pk:
        reg_num_query = reg_num_query.exclude(pk=ngo.pk)

    if reg_num_query.exists():
        return f'CIF "{registration_number}" este înregistrat deja'

    return ""


def delete_prefilled_form(ngo_id):
    return Ngo.delete_prefilled_form(ngo_id)
