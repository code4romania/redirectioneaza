from typing import Callable, Dict, List, Optional, Union

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django_q.tasks import async_task

from redirectioneaza.common.filters import QueryFilter
from users.models import User

from ..common.validation.registration_number import extract_vat_id, ngo_id_number_validator
from ..forms.ngo_account import CauseForm, NgoPresentationForm
from ..models.donors import Donor
from ..models.jobs import Job
from ..models.ngos import Cause, Ngo
from .base import BaseContextPropertiesMixin, BaseVisibleTemplateView
from .common.misc import get_ngo_archive_download_status
from .common.search import DonorSearchMixin
from .ngo_account_filters import (
    CountyQueryFilter,
    FormPeriodQueryFilter,
    FormStatusQueryFilter,
    LocalityQueryFilter,
)

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


def get_ngo_cause_banner_list_items(ngo: Ngo) -> List[str]:
    banner_list_items = [
        _("Organization name: ") + ngo.name,
        _("Organization CIF: ") + ngo.registration_number,
    ]
    return banner_list_items


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

            if form.cleaned_data["logo"]:
                ngo.logo = form.cleaned_data["logo"]

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
            async_task(delete_prefilled_form, ngo.id)

        # XXX: [MULTI-FORM] remove these once we have multiple forms
        if ngo.causes.exists():
            cause: Cause = ngo.causes.first()
            cause.sync_with_ngo()

        context["ngo"] = ngo

        return render(request, self.template_name, context)


class NgoMainCauseView(NgoBaseTemplateView):
    template_name = "ngo-account/my-organization/ngo-form.html"
    title = _("Organization form")
    tab_title = "form"
    sidebar_item_target = "org-data"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo: Ngo = context["ngo"]

        cause_url = ""
        if ngo and ngo.causes.exists():
            cause = ngo.causes.first()
            cause_url = self.request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": cause.slug}))

        cause = None
        if ngo:
            cause = Cause.objects.filter(ngo=ngo).first()

        context.update(
            {
                "ngo_url": cause_url,
                "cause": cause,
                "active_tab": self.tab_title,
                "info_banner_items": get_ngo_cause_banner_list_items(ngo),
            }
        )

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user: User = request.user

        if not user.ngo:
            return redirect(reverse("my-organization:presentation"))

        return super().get(request, *args, **kwargs)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST
        user: User = request.user

        if not user.is_authenticated:
            raise PermissionDenied()

        context = self.get_context_data()

        ngo: Ngo = user.ngo

        must_refresh_prefilled_form = False

        cause: Cause = Cause.objects.filter(ngo=ngo).first()
        if cause is None:
            cause = Cause(ngo=ngo, is_main=True)
        form = CauseForm(post, instance=cause)

        context.update({"django_form": form})

        if not form.is_valid():
            messages.error(request, _("There are some errors on the redirection form."))
            return render(request, self.template_name, context)

        cause = form.save(commit=True)

        # XXX: [MULTI-FORM] Remove once testing is finished, this information should only be kept in the forms
        cause.sync_with_ngo(force_cause_save=True)

        if must_refresh_prefilled_form:
            async_task(delete_prefilled_form, ngo.id)

        context["ngo"] = ngo
        context["cause"] = cause

        return render(request, self.template_name, context)


class NgoCausesListView(NgoBaseListView):
    template_name = "ngo-account/causes/main.html"
    title = _("Organization Causes")
    context_object_name = "causes"
    paginate_by = 8
    sidebar_item_target = "org-causes"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user: User = self.request.user

        if not user.ngo:
            return Cause.objects.none()

        return Cause.other.filter(ngo=user.ngo).order_by("date_created")


class NgoCausesView(NgoBaseTemplateView):
    template_name = "ngo-account/cause/main.html"
    title = _("Organization form")
    sidebar_item_target = "org-causes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        cause_create_path = reverse("my-organization:cause-create")

        ngo = context["ngo"]

        cause = None
        cause_id = kwargs.get("cause_id")
        if request.path != cause_create_path:
            if not cause_id:
                raise Http404

            cause = Cause.objects.filter(pk=cause_id, ngo=ngo).first()
            if not cause:
                raise Http404

        context.update(
            {
                "cause": cause,
                "active_regions": settings.FORM_COUNTIES_NATIONAL,
                "counties": settings.LIST_OF_COUNTIES,
                "info_banner_items": get_ngo_cause_banner_list_items(ngo),
            }
        )

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        post = request.POST
        user: User = request.user

        ngo: Ngo = user.ngo

        if not ngo:
            return redirect(reverse("my-organization:presentation"))

        existing_cause = context.get("cause")
        form = CauseForm(post, instance=existing_cause)

        context.update({"django_form": form})

        if not form.is_valid():
            messages.error(request, _("There are some errors on the redirection form."))
            return render(request, self.template_name, context)

        cause = form.save(commit=False)
        cause.ngo = ngo
        cause.save()

        context["cause"] = cause
        context["ngo"] = ngo

        success_message = _("The cause has been created.")
        if existing_cause:
            success_message = _("The changes have been saved.")
        messages.success(request, success_message)

        return redirect(reverse_lazy("my-organization:cause", kwargs={"cause_id": cause.pk}))


class UserSettingsView(NgoBaseTemplateView):
    template_name = "ngo-account/settings-account/main.html"
    title = _("Account settings")
    sidebar_item_target = "user-settings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        has_ngohub = None
        if ngo:
            has_ngohub = ngo.ngohub_org_id is not None

        context.update(
            {
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


class NgoRedirectionsView(NgoBaseListView, DonorSearchMixin):
    template_name = "ngo-account/redirections/main.html"
    title = _("Redirections")
    context_object_name = "redirections"
    paginate_by = 8
    sidebar_item_target = "org-redirections"

    def get_filters(self) -> List[QueryFilter]:
        return [
            CountyQueryFilter(),
            LocalityQueryFilter(),
            FormPeriodQueryFilter(),
            FormStatusQueryFilter(),
        ]

    def get_filters_dict(self) -> List[Dict[str, Union[str, Callable, Optional[List[Dict]]]]]:
        objects = self.object_list
        return [query_filter.to_dict(include_options=True, objects=objects) for query_filter in (self.get_filters())]

    def get_frontend_filters(self, filters: List[QueryFilter] = None):
        if not filters:
            filters = self.get_filters()

        filters_active = {}
        request_params = self.request.GET

        for search_filter in filters:
            filter_key = search_filter.key
            if filter_value := request_params.get(filter_key, ""):
                filters_active[filter_key] = filter_value

        return filters_active

    def get_queryset_filters(self, filters: List[QueryFilter] = None):
        if not filters:
            filters = self.get_filters()

        queryset_filters = {}
        request_params = self.request.GET

        for search_filter in filters:
            filter_key = search_filter.key
            if filter_value := request_params.get(filter_key, ""):
                queryset_filters[search_filter.queryset_key] = search_filter.transform(filter_value)

        return queryset_filters

    def get_context_data(self, **kwargs):
        search_query = self._search_query()

        query_dict = QueryDict(mutable=True)
        query_dict["q"] = search_query

        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "search_query": search_query,
                "url_search_query": query_dict.urlencode(),
                "filters": self.get_filters_dict(),
                "filters_active": self.get_frontend_filters(),
            }
        )

        if search_placeholder := self._search_placeholder():
            context["search_placeholder"] = search_placeholder

        context.update(get_ngo_archive_download_status(ngo))

        return context

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        if not ngo:
            return Donor.objects.none()

        queryset_filters = self.get_queryset_filters()

        redirections = (
            ngo.donor_set.all()
            .order_by("-date_created")
            .filter(is_available=True)
            .filter(**queryset_filters)
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

        return self.search(queryset=redirections)


class NgoArchivesView(NgoBaseListView):
    template_name = "ngo-account/archives/main.html"
    title = _("Archives history")
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

        archives = Job.objects.none()
        if ngo:
            archives = (
                ngo.jobs.all()
                .order_by("-date_created")
                .values(
                    "pk",
                    "date_created",
                    "number_of_donations",
                    "status",
                )
            )

        return archives


class RedirectionDownloadLinkView(BaseVisibleTemplateView):
    title = _("Download donor form")

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, form_id, *args, **kwargs):
        user: User = request.user
        ngo: Ngo = user.ngo if user.ngo else None

        if not ngo:
            raise Http404

        if not ngo.is_active:
            raise PermissionDenied(_("Your organization is not active"))

        try:
            donor = Donor.objects.get(pk=form_id, ngo=ngo)
        except Donor.DoesNotExist:
            raise Http404

        if not donor.pdf_file:
            raise Http404

        return redirect(donor.pdf_file.url)


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
                job = Job.objects.get(pk=job_id, ngo=user.ngo)
            except Job.DoesNotExist:
                raise Http404

        # Check that the job has a zip file
        if not job.zip:
            raise Http404

        return redirect(job.zip.url)
