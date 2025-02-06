from typing import List, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django_q.tasks import async_task

from users.models import User

from ..common.validation.registration_number import extract_vat_id, ngo_id_number_validator
from ..forms.ngo_account import NgoFormForm, NgoPresentationForm
from ..models.donors import Donor
from ..models.jobs import Job
from ..models.ngos import Ngo
from .api import CheckNgoUrl
from .base import BaseContextPropertiesMixin, BaseVisibleTemplateView
from .common import get_ngo_archive_download_status

UserModel = get_user_model()


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


class NgoBaseView(BaseContextPropertiesMixin):
    title = _("Organization details")
    sidebar_item_target = None

    def get_extra_context(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        return {
            "user": user,
            "ngo": ngo,
            "title": self._get_checked_property("title", ""),
            "active_item": self._get_checked_property("sidebar_item_target", ""),
        }


class NgoBaseTemplateView(NgoBaseView, BaseVisibleTemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_extra_context())

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NgoBaseListView(NgoBaseView, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_extra_context())

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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

        context.update(
            {
                "counties": settings.FORM_COUNTIES_NATIONAL,
                "has_ngohub": has_ngohub,
                "ngohub_url": ngohub_url,
                "active_tab": self.tab_title,
            }
        )

        return context

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

            ngo.logo = form.cleaned_data["logo"]

            ngo.website = form.cleaned_data["website"]
            ngo.address = form.cleaned_data["address"]
            ngo.county = form.cleaned_data["county"]
            ngo.locality = form.cleaned_data["locality"]
            ngo.active_region = form.cleaned_data["active_region"]

        ngo.is_accepting_forms = form.cleaned_data["is_accepting_forms"]
        ngo.display_email = form.cleaned_data["display_email"]
        ngo.display_phone = form.cleaned_data["display_phone"]

        if errors:
            return render(request, self.template_name, context)

        ngo.save()

        if is_new_ngo:
            user.ngo = ngo
            user.save()
        elif must_refresh_prefilled_form:
            async_task("donations.views.ngo_account.delete_prefilled_form", ngo.id)

        context["ngo"] = ngo

        return render(request, self.template_name, context)


class NgoFormsView(NgoBaseTemplateView):
    template_name = "ngo-account/my-organization/ngo-form.html"
    title = _("Organization forms")
    tab_title = "form"
    sidebar_item_target = "org-data"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo: Ngo = context["ngo"]

        ngo_url = ""
        if ngo and ngo.slug:
            ngo_url = self.request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": ngo.slug}))

        context.update(
            {
                "ngo_url": ngo_url,
                "active_tab": self.tab_title,
            }
        )

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.ngo:
            return redirect(reverse("my-organization:presentation"))

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

        form = NgoFormForm(post)

        if not form.is_valid():
            messages.error(request, _("There are some errors on the redirection form."))
            context.update({"ngo_form": form})
            return render(request, self.template_name, context)

        slug_has_errors = False

        form_slug = form.cleaned_data["slug"]
        if CheckNgoUrl().check_slug_is_blocked(form_slug):
            slug_has_errors = True
            form.add_error("slug", ValidationError(_("The URL is blocked")))

        if CheckNgoUrl().check_slug_is_reused(form_slug, user):
            slug_has_errors = True
            form.add_error("slug", ValidationError(_("The URL is already used")))

        if slug_has_errors:
            context["ngo_form"] = form
            return render(request, self.template_name, context)

        ngo.slug = form_slug

        ngo.bank_account = form.cleaned_data["iban"]
        ngo.description = form.cleaned_data["description"]

        if errors:
            return render(request, self.template_name, context)

        ngo.save()

        if must_refresh_prefilled_form:
            async_task("donations.views.my_account.delete_prefilled_form", ngo.id)

        context["ngo"] = ngo

        return render(request, self.template_name, context)


class NgoSettingsView(NgoBaseTemplateView):
    template_name = "ngo-account/settings/main.html"
    title = _("Organization settings")
    sidebar_item_target = "org-settings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        has_ngohub = None
        if ngo:
            has_ngohub = ngo.ngohub_org_id is not None

        context.update(
            {
                "counties": settings.FORM_COUNTIES_NATIONAL,
                "has_ngohub": has_ngohub,
            }
        )

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        if context["has_ngohub"]:
            return render(request, self.template_name, context)

        post = request.POST

        user: UserModel = request.user
        user.last_name = post.get("first_name")
        user.first_name = post.get("last_name")

        user.save()

        context["user"] = user

        return render(request, self.template_name, context)


class NgoRedirectionsView(NgoBaseListView):
    template_name = "ngo-account/redirections/main.html"
    title = _("Redirections")
    context_object_name = "redirections"
    paginate_by = 8
    sidebar_item_target = "org-redirections"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
            }
        )

        context.update(get_ngo_archive_download_status(ngo))

        return context

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        redirections = Donor.objects.none()
        if ngo:
            redirections = (
                ngo.donor_set.all()
                .order_by("-date_created")
                .values(
                    "id",
                    "f_name",
                    "l_name",
                    "city",
                    "county",
                    "email",
                    "phone",
                    "date_created",
                    "two_years",
                    "is_anonymous",
                    "has_signed",
                )
            )

        return redirections


class NgoArchivesView(NgoBaseListView):
    template_name = "ngo-account/archives/main.html"
    title = _("Archives history ")
    context_object_name = "archive_jobs"
    paginate_by = 8
    sidebar_item_target = "org-archives"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
            }
        )

        return context

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        redirections = Job.objects.none()
        if ngo:
            redirections = (
                ngo.jobs.all()
                .order_by("-date_created")
                .values(
                    "pk",
                    "date_created",
                    "status",
                )
            )

        return redirections


# TODO: Figure out how to optimize it and if it does anything else than redirecting to the zip file
class ArchiveDownloadLinkView(BaseVisibleTemplateView):
    title = _("Download archive")

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request: HttpRequest, job_id, *args, **kwargs):
        user: User = request.user

        if user.has_perm("users.can_view_old_dashboard"):
            # The admin can always get the download link
            try:
                job = Job.objects.get(pk=job_id)
            except Job.DoesNotExist:
                raise Http404

        elif not user.ngo:
            # Users without NGOs don't have any download links anyway
            raise Http404

        else:
            # Check that the current user's NGO is active
            if not user.ngo.is_active:
                raise Http404

            # Check that the requested job belongs to the current user
            try:
                job = Job.objects.get(pk=job_id, ngo=user.ngo, owner=user)
            except Job.DoesNotExist:
                raise Http404

        # Check that the job has a zip file
        if not job.zip:
            raise Http404

        return redirect(job.zip.url)
