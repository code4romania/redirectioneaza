import logging
from typing import Any, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.forms import BaseForm
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from donations.forms.ngo_account import CauseForm
from donations.models.ngos import Cause, CauseVisibilityChoices, Ngo
from donations.views.ngo_account.common import NgoBaseListView, NgoBaseTemplateView, delete_cause_prefilled_form
from redirectioneaza.common.async_wrapper import async_wrapper
from users.models import User

logger = logging.getLogger(__name__)


class NgoCauseCommonView(NgoBaseTemplateView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_main_cause = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo: Ngo = context["ngo"]

        context["info_banner_items"] = self.get_ngo_cause_banner_list_items(ngo)
        context["visibility_choices"] = CauseVisibilityChoices.as_str_pretty()

        return context

    def get_ngo_cause_banner_list_items(self, ngo: Ngo) -> List[str]:
        banner_list_items = [
            _("Organization name: ") + ngo.name,
            _("Organization CIF: ") + ngo.registration_number,
        ]
        return banner_list_items

    def _check_field_altered(self, form: BaseForm, field_name: str, expected_value: Any) -> None:
        """
        Check if a field in the form has been altered from its expected value.
        """
        user_error_message = _("The form was altered.")

        if field_name not in form.cleaned_data:
            logger.error(f"The parameter '{field_name}' was altered and is missing from the form")
            raise ValidationError(user_error_message)

        if form.cleaned_data[field_name] != expected_value:
            logger.error(f"The parameter '{field_name}' was altered with value {form.cleaned_data[field_name]}")
            raise ValidationError(user_error_message)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def do_post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)

        response = {
            "status": "error",
        }

        post = request.POST
        user: User = request.user

        ngo: Ngo = user.ngo

        must_refresh_prefilled_form = False

        if not ngo:
            messages.error(request, _("Please fill in the organization details first."))
            response["error"] = redirect(reverse("my-organization:presentation"))
            return response

        if not self.is_main_cause and not ngo.can_create_causes:
            messages.error(request, _("You need to first create the form with the organization's details."))
            response["error"] = redirect(reverse("my-organization:presentation"))
            return response

        existing_cause: Cause = context.get("cause")

        existing_bank_account = None
        if existing_cause and existing_cause.bank_account:
            existing_bank_account = existing_cause.bank_account

        form = CauseForm(post, for_main_cause=self.is_main_cause, files=request.FILES, instance=existing_cause)
        context["django_form"] = form

        if not form.is_valid():
            messages.error(request, _("There are some errors on the redirection form."))
            response["error"] = render(request, self.template_name, context)
            return response

        if existing_bank_account != form.cleaned_data["bank_account"]:
            must_refresh_prefilled_form = True

        cause = form.save(commit=False)
        cause.ngo = ngo
        cause.save()

        if must_refresh_prefilled_form:
            async_wrapper(delete_cause_prefilled_form, cause.pk)

        context["cause"] = cause
        context["ngo"] = ngo
        context["django_form"] = form

        success_message = _("The cause has been created.")
        if existing_cause:
            # Formularul a fost salvat cu succes!
            success_message = _("The form has been saved.")
        messages.success(request, success_message)

        response["status"] = "success"
        response["context"] = context

        return response


class NgoCausesListView(NgoBaseListView):
    template_name = "ngo-account/causes/main.html"
    title = _("Organization Causes")
    context_object_name = "causes"
    paginate_by = 8
    sidebar_item_target = "org-causes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["absolute_path"] = self.request.build_absolute_uri("/")

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        if not request.user.ngo:
            messages.error(request, _("You need to add your NGO's information first."))
            return redirect(reverse("my-organization:presentation"))

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user: User = self.request.user

        if not user.ngo:
            return Cause.objects.none()

        return Cause.other.filter(ngo=user.ngo).order_by("date_created")


class NgoCauseCreateView(NgoCauseCommonView):
    template_name = "ngo-account/cause/main.html"
    title = _("Organization form")
    sidebar_item_target = "org-causes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page_title = _("Add new cause form")

        context["page_title"] = page_title
        context["breadcrumbs"] = [
            {
                "url": reverse_lazy("my-organization:causes"),
                "title": _("Causes"),
            },
            {
                "title": page_title,
            },
        ]

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user: User = request.user

        if user.ngo and not user.ngo.can_create_causes:
            messages.error(request, _("You need to first create the form with the organization's details."))
            return redirect(reverse("my-organization:form"))

        return super().get(request, *args, **kwargs)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        response = self.do_post(request, *args, **kwargs)

        if response["status"] == "error":
            return response["error"]

        cause: Cause = response["context"]["cause"]

        return redirect(reverse_lazy("my-organization:cause", kwargs={"cause_id": cause.pk}))


class NgoCauseEditView(NgoCauseCommonView):
    template_name = "ngo-account/cause/main.html"
    title = _("Organization form")
    sidebar_item_target = "org-causes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        page_title = _("Edit cause")

        context["cause"] = self.get_cause(cause_id=kwargs["cause_id"], ngo=context["ngo"])
        context["django_form"] = CauseForm(instance=context["cause"], for_main_cause=self.is_main_cause)

        context["page_title"] = f"{page_title}: \"{context['cause'].name}\""
        context["breadcrumbs"] = [
            {
                "url": reverse_lazy("my-organization:causes"),
                "title": _("Causes"),
            },
            {
                "title": page_title,
            },
        ]

        return context

    def get_cause(self, cause_id: int, ngo: Ngo) -> Cause:
        if not ngo:
            raise Http404

        if not cause_id:
            raise Http404

        cause = Cause.objects.filter(pk=cause_id, ngo=ngo).first()
        if not cause:
            raise Http404

        return cause

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        response = self.do_post(request, *args, **kwargs)

        if response["status"] == "error":
            return response["error"]

        return render(request, self.template_name, response["context"])
