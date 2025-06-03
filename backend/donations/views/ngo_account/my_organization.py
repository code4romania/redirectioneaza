from typing import List

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from donations.common.validation.registration_number import extract_vat_id
from donations.forms.ngo_account import CauseForm, NgoPresentationForm
from donations.models.ngos import Cause, Ngo
from donations.views.ngo_account.causes import NgoCauseCommonView
from donations.views.ngo_account.common import NgoBaseTemplateView, delete_ngo_prefilled_forms
from redirectioneaza.common.async_wrapper import async_wrapper
from users.models import User


class NgoPresentationView(NgoBaseTemplateView):
    template_name = "ngo-account/my-organization/ngo-presentation.html"
    title = _("Organization details")
    tab_title = "presentation"
    sidebar_item_target = "org-data"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        has_ngohub = None
        if ngo:
            has_ngohub = ngo.ngohub_org_id is not None

        ngohub_url = ""
        if has_ngohub:
            ngohub_url = f"{settings.NGOHUB_APP_BASE}organizations/{ngo.ngohub_org_id}/general"

        if missing_fields := self.get_missing_fields(
            source="ngo",
            ngo=context.get("ngo"),
            cause=context.get("cause"),
        ):
            context["missing_fields"] = missing_fields

        context.update(
            {
                "active_regions": settings.FORM_COUNTIES_NATIONAL,
                "counties": settings.LIST_OF_COUNTIES,
                "has_ngohub": has_ngohub,
                "ngohub_url": ngohub_url,
                "active_tab": self.tab_title,
            }
        )

        return context

    def get(self, request, *args, **kwargs):
        user: User = request.user

        if user.is_staff:
            if user.partner:
                return redirect(reverse_lazy("admin:partners_partner_change", args=[user.partner.pk]))
            if user.is_superuser:
                return redirect(reverse("admin:index"))

        return super().get(request, *args, **kwargs)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied()

        context = self.get_context_data()

        errors: List[str] = []

        ngo: Ngo = user.ngo

        must_refresh_prefilled_form = False
        is_new_ngo = False

        if not ngo:
            is_new_ngo = True

            ngo = Ngo()

            ngo.is_verified = False
            ngo.is_active = True

        is_fully_editable = ngo.ngohub_org_id is None

        form = NgoPresentationForm(post, files=request.FILES, is_fully_editable=is_fully_editable, ngo=ngo)
        if not form.is_valid():
            messages.error(request, _("There are some errors on the presentation form."))
            context.update({"ngo_presentation": form})

            return render(request, self.template_name, context)

        if is_fully_editable:
            vat_information = extract_vat_id(form.cleaned_data["cif"])
            if ngo.registration_number != vat_information["registration_number"]:
                ngo.registration_number = vat_information["registration_number"]
                must_refresh_prefilled_form = True

            if ngo.vat_id != vat_information["vat_id"]:
                ngo.vat_id = vat_information["vat_id"]
                must_refresh_prefilled_form = True

            if ngo.name != form.cleaned_data["name"]:
                ngo.name = form.cleaned_data["name"]
                must_refresh_prefilled_form = True

            ngo.phone = form.cleaned_data["contact_phone"]
            ngo.email = form.cleaned_data["contact_email"]

            ngo.website = form.cleaned_data["website"]
            ngo.address = form.cleaned_data["address"]
            ngo.county = form.cleaned_data["county"]
            ngo.locality = form.cleaned_data["locality"]
            ngo.active_region = form.cleaned_data["active_region"]

        ngo.display_email = form.cleaned_data["display_email"]
        ngo.display_phone = form.cleaned_data["display_phone"]

        if errors:
            return render(request, self.template_name, context)

        ngo.save()

        if is_new_ngo:
            user.ngo = ngo
            user.save()
        elif must_refresh_prefilled_form:
            async_wrapper(delete_ngo_prefilled_forms, ngo.id)

        context["ngo"] = ngo

        return render(request, self.template_name, context)


class NgoMainCauseView(NgoCauseCommonView):
    template_name = "ngo-account/my-organization/ngo-form.html"
    title = _("Organization form")
    tab_title = "form"
    sidebar_item_target = "org-data"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_main_cause = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(is_main_cause=True, **kwargs)

        context["cause"] = self.get_main_cause(context.get("ngo"))
        context["is_main_cause"] = self.is_main_cause

        context["django_form"] = CauseForm(instance=context["cause"], for_main_cause=self.is_main_cause)

        if missing_fields := self.get_missing_fields(
            source="cause",
            ngo=context.get("ngo"),
            cause=context.get("cause"),
        ):
            context["missing_fields"] = missing_fields

        context["active_tab"] = self.tab_title

        return context

    def get_main_cause(self, ngo: Ngo) -> Cause:
        return Cause.objects.filter(ngo=ngo, is_main=True).first()

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user: User = request.user

        if not user.ngo:
            return redirect(reverse("my-organization:presentation"))

        return super().get(request, *args, **kwargs)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        response = self.do_post(request, *args, **kwargs)

        if response["status"] == "error":
            return response["error"]

        return render(request, self.template_name, response["context"])
