from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import QuerySet
from django.db.models.base import ModelBase
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from donations.models.ngos import Cause, Ngo
from donations.views.base import BaseContextPropertiesMixin, BaseVisibleTemplateView
from users.models import User
from utils.text.registration_number import ngo_id_number_validator


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
        ngo: Ngo | None,
        cause: Cause | None,
    ) -> dict[str, str] | None:
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

    def get_cause_missing_fields(self, cause: Cause | None) -> list[str] | None:
        if not cause:
            missing_fields = Cause.mandatory_fields_names_capitalized()
        else:
            missing_fields = cause.missing_mandatory_fields_names_capitalized()

        return missing_fields

    def get_missing_ngo_fields(self, ngo: Ngo | None) -> list[str] | None:
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


def validate_iban(bank_account) -> str | None:
    if not bank_account:
        return None

    if len(bank_account) != 24:
        return _("The IBAN number must have 24 characters")

    if not bank_account.isalnum():
        return _("The IBAN number must contain only letters and digits")

    if not bank_account.startswith("RO"):
        return _("The IBAN number must start with 'RO'")

    return None


def validate_registration_number(ngo, registration_number) -> str | None:
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


def delete_ngo_prefilled_forms(ngo_id: int):
    """
    Delete prefilled forms associated with the given NGO ID.
    :param ngo_id: The ID of the NGO whose prefilled forms are to be deleted.
    :return: The result of the deletion operation.
    """

    return Ngo.delete_prefilled_form(ngo_id)


def delete_cause_prefilled_form(cause_id):
    """
    Deletes a prefilled form associated with a specific cause.

    This function acts as a wrapper around the `Cause.delete_prefilled_form` method,
    which performs the actual deletion of the prefilled form.

    :param cause_id: The ID of the cause whose prefilled form is to be deleted.
    :return: The result of the `Cause.delete_prefilled_form` method.
    """
    cause: Cause = Cause.objects.filter(pk=cause_id).first()
    if not cause:
        return None
    return cause.delete_prefilled_form()


class FileDownloadProxy(BaseVisibleTemplateView):
    """
    This class is used to download files from the server.
    It is used for downloading the CSV files generated by the system.
    """

    title = _("Download generated file")
    model: ModelBase | None = None

    def is_user_valid(self, user: User) -> bool:
        """
        Check if the user is valid.
        This means that the user is not anonymous, and either a staff member or a user of an active NGO.
        :param user: The user to check.
        :return: True if the user is valid, False otherwise.
        """
        if user.is_anonymous:
            return False

        if user.is_staff:
            return True

        if user.ngo and user.ngo.is_active:
            return True
        return False

    def get_downloadable_object(self, user: User, pk: int):
        """
        Get the NGO document for the user.
        :param user: The user to check.
        :param pk: The primary key of the document.
        :return: The NGO document if it exists, None otherwise.
        """
        queryset = {"pk": pk}

        if ngo := user.ngo:
            queryset["ngo"] = ngo

        try:
            result = self.model.objects.get(**queryset)
        except ObjectDoesNotExist:
            return None

        return result
