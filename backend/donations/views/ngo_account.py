import datetime
from collections import OrderedDict
from typing import List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django_q.tasks import async_task

from redirectioneaza.common.cache import cache_decorator
from users.models import User

from ..common.validation.registration_number import clean_registration_number, extract_vat_id, ngo_id_number_validator
from ..models.donors import Donor
from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import Ngo
from .api import CheckNgoUrl
from .base import BaseVisibleTemplateView

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


class MyAccountDetailsView(BaseVisibleTemplateView):
    template_name = "ngo/my-account-details.html"
    title = _("My Account Details")

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user
        is_ngohub_user: bool = user.is_ngohub_user

        context = {"user": user, "is_ngohub_user": is_ngohub_user}
        return render(request, self.template_name, context)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST

        user: UserModel = request.user
        user.last_name = post.get("nume")
        user.first_name = post.get("prenume")

        user.save()

        context = {"user": user}

        return render(request, self.template_name, context)


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


class MyAccountView(BaseVisibleTemplateView):
    template_name = "ngo/my-account.html"
    title = _("My Account")

    @staticmethod
    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix="DONORS_BY_DONATION_YEAR")
    def _get_donors_by_donation_year(ngo: Ngo) -> OrderedDict[int, QuerySet[Donor]]:
        if not ngo:
            return OrderedDict()

        donation_years = list(range(timezone.now().year, ngo.date_created.year - 1, -1))

        donors_grouped_by_year = OrderedDict()
        for donation_year in donation_years:
            donors_grouped_by_year[donation_year] = Donor.objects.filter(
                ngo=ngo, date_created__year=donation_year
            ).order_by("-date_created")

        return donors_grouped_by_year

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request: HttpRequest, *args, **kwargs):
        user: User = request.user

        if user.has_perm("users.can_view_old_dashboard"):
            return redirect(reverse("admin-ngos"))

        user_ngo: Ngo = user.ngo if user.ngo else None

        now = timezone.now()

        grouped_donors: OrderedDict[int, QuerySet[Donor]] = self._get_donors_by_donation_year(ngo=user_ngo)
        current_year_donors: Optional[QuerySet[Donor]] = grouped_donors.get(now.year)
        donors_metadata = {
            "total": current_year_donors.count() if current_year_donors else 0,
            "total_signed": (current_year_donors.filter(has_signed=True).count() if current_year_donors else 0),
            "years": list(grouped_donors.keys()),
        }

        download_expired = not now.date() > settings.DONATIONS_LIMIT + datetime.timedelta(
            days=settings.TIMEDELTA_DONATIONS_LIMIT_DOWNLOAD_DAYS
        )

        ngo_url = ""
        if user_ngo and user_ngo.slug:
            ngo_url = request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": user_ngo.slug}))

        ngo_jobs = user_ngo.jobs.all()[:10] if user_ngo else None

        last_job_was_recent = False
        if ngo_jobs:
            last_job_date = ngo_jobs[0].date_created
            last_job_status = ngo_jobs[0].status

            timedelta = datetime.timedelta(0)
            if last_job_status != JobStatusChoices.ERROR:
                timedelta = datetime.timedelta(minutes=settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES)

            if last_job_date > now - timedelta:
                last_job_was_recent = True

        has_signed_form = user_ngo.is_accepting_forms if user_ngo else False

        disable_forms_download = False
        disable_past_download = False
        if not user_ngo or not user_ngo.is_active:
            disable_forms_download = True
            disable_past_download = True
        elif settings.ENABLE_FORMS_DOWNLOAD and (not has_signed_form or not download_expired or last_job_was_recent):
            disable_forms_download = True

        context = {
            "user": user,
            "jobs": ngo_jobs,
            "limit": settings.DONATIONS_LIMIT,
            "ngo": user_ngo,
            "donors": grouped_donors,
            "donor_metadata": donors_metadata,
            "counties": settings.FORM_COUNTIES_NATIONAL,
            "disable_new_download": disable_forms_download,
            "disable_past_download": disable_past_download,
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            "minutes_between_retries": settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES,
            "has_signed_form": has_signed_form,
            "current_year": now.year,
            "ngo_url": ngo_url,
        }

        return render(request, self.template_name, context)


def delete_prefilled_form(ngo_id):
    return Ngo.delete_prefilled_form(ngo_id)


class NgoBaseView(BaseVisibleTemplateView):
    title = _("Organization details")
    tab_title = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "current_tab": self.tab_title,
            }
        )

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        return render(request, self.template_name, context)


class NgoFormsView(NgoBaseView):
    template_name = "ngo-account/my-organization/ngo-form.html"
    title = _("Organization forms")
    tab_title = "form"
    sidebar_item_target = "data"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo: Ngo = context["ngo"]

        ngo_url = ""
        if ngo and ngo.slug:
            ngo_url = self.request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": ngo.slug}))

        context.update(
            {
                "ngo_url": ngo_url,
                "active_item": self.sidebar_item_target,
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

        ngo_slug = post.get("organization-slug", "").strip().lower()
        ngo_slug_errors = CheckNgoUrl.validate_ngo_slug(user, ngo_slug)
        ngo.slug = ngo_slug

        if isinstance(ngo_slug_errors, HttpResponseBadRequest):
            errors.append(_("The URL is already used"))

        bank_account = post.get("iban", "").strip().upper().replace(" ", "").replace("<", "").replace(">", "")[:34]
        bank_account_errors: str = validate_iban(bank_account)
        if ngo.bank_account != bank_account:
            ngo.bank_account = bank_account
            must_refresh_prefilled_form = True

        ngo.description = post.get("description", "").strip()

        if bank_account_errors:
            errors.append(bank_account_errors)

        if errors:
            return render(request, self.template_name, context)

        ngo.save()

        if must_refresh_prefilled_form:
            async_task("donations.views.my_account.delete_prefilled_form", ngo.id)

        context["ngo"] = ngo

        return render(request, self.template_name, context)


class NgoDetailsView(NgoBaseView):
    template_name = "ngo-account/my-organization/ngo-presentation.html"
    title = _("Organization details")
    tab_title = "presentation"
    sidebar_item_target = "data"

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
                "active_item": self.sidebar_item_target,
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

        if is_fully_editable:
            registration_number = clean_registration_number(post.get("cif", ""))
            registration_number_errors: str = validate_registration_number(ngo, registration_number)

            if registration_number_errors:
                errors.append(registration_number_errors)

            vat_information = extract_vat_id(registration_number)

            if ngo.registration_number != vat_information["registration_number"]:
                ngo.registration_number = vat_information["registration_number"]
                must_refresh_prefilled_form = True

            if ngo.vat_id != vat_information["vat_id"]:
                ngo.vat_id = vat_information["vat_id"]
                must_refresh_prefilled_form = True

            ngo_name = post.get("name", "").strip()
            if ngo.name != ngo_name:
                ngo.name = ngo_name

            ngo.phone = post.get("contact-phone", "").strip()
            ngo.email = post.get("contact-email", "").strip()

            ngo.website = post.get("website", "").strip()
            ngo.address = post.get("address", "").strip()
            ngo.county = post.get("county", "").strip()
            ngo.active_region = post.get("active-region", "").strip()

        ngo.display_email = post.get("display-email", "").strip() == "on"
        ngo.display_phone = post.get("display-phone", "").strip() == "on"

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


class OldNgoDetailsView(BaseVisibleTemplateView):
    template_name = "ngo/ngo-details.html"
    title = _("Organization details")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "title": "Date organizație",
                "counties": settings.FORM_COUNTIES_NATIONAL,
                "user": user,
                "ngo": ngo,
            }
        )

        if not ngo:
            return context

        context.update(
            {
                "has_ngohub": ngo.ngohub_org_id is not None,
            }
        )

        return context

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.has_perm("users.can_view_old_dashboard"):
            return redirect(reverse("admin-ngos"))

        if not user.is_authenticated or not user.ngo:
            return redirect(reverse("contul-meu"))

        context = self.get_context_data(**kwargs)

        return render(request, self.template_name, context)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied()

        if user.has_perm("users.can_view_old_dashboard"):
            ngo_url = post.get("old-ong-url", "")

            try:
                user.ngo = Ngo.objects.get(slug=ngo_url)
            except Ngo.DoesNotExist:
                raise Http404()

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

        bank_account = post.get("ong-cont", "").strip().upper().replace(" ", "").replace("<", "").replace(">", "")[:34]
        bank_account_errors: str = self._validate_iban_number(bank_account)
        if ngo.bank_account != bank_account:
            ngo.bank_account = bank_account
            must_refresh_prefilled_form = True

        ngo_slug = post.get("ong-url", "").strip().lower()
        ngo_slug_errors = CheckNgoUrl.validate_ngo_slug(user, ngo_slug)
        ngo.slug = ngo_slug

        ngo.description = post.get("ong-descriere", "").strip()
        ngo.is_accepting_forms = True if post.get("accepts-forms") == "on" else False

        if is_fully_editable:
            registration_number = (
                post.get("ong-cif", "").upper().replace(" ", "").replace("<", "").replace(">", "")[:20]
            )
            registration_number_errors: str = self._validate_registration_number(ngo, registration_number)
            if ngo.registration_number != registration_number:
                ngo.registration_number = registration_number
                must_refresh_prefilled_form = True

            ngo_name = post.get("ong-nume", "").strip()
            if ngo.name != ngo_name:
                ngo.name = ngo_name
                must_refresh_prefilled_form = True

            ngo.phone = post.get("ong-tel", "").strip()
            ngo.email = post.get("ong-email", "").strip()
            ngo.website = post.get("ong-website", "").strip()
            ngo.address = post.get("ong-adresa", "").strip()
            ngo.county = post.get("ong-judet", "").strip()
            ngo.active_region = post.get("ong-activitate", "").strip()
            ngo.is_social_service_viable = True if post.get("social-service") == "on" else False

            if registration_number_errors:
                errors.append(registration_number_errors)

        if bank_account_errors:
            errors.append(bank_account_errors)

        if isinstance(ngo_slug_errors, HttpResponseBadRequest):
            errors.append(_("The URL is already used"))

        context = self.get_context_data()
        if errors:
            return render(request, self.template_name, context)

        if request.user.has_perm("users.can_view_old_dashboard"):
            ngo.is_verified = post.get("ong-verificat") == "on"
            ngo.is_active = post.get("ong-activ") == "on"

        if new_ngo_owner := post.get("new-ngo-owner"):
            change_owner_result = self.change_ngo_owner(ngo, new_ngo_owner)

            if "error" in change_owner_result:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))

        ngo.save()

        # Delete the NGO's old prefilled form
        if must_refresh_prefilled_form:
            async_task("donations.views.my_account.delete_prefilled_form", ngo.id)

        if is_new_ngo:
            user.ngo = ngo
            user.save()

        if request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))

        return render(request, self.template_name, context)

    @staticmethod
    def _validate_registration_number(ngo, registration_number) -> Optional[str]:
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

    @staticmethod
    def _validate_iban_number(bank_account) -> Optional[str]:
        if not bank_account:
            return None

        if len(bank_account) != 24:
            return _("The IBAN number must have 24 characters")

        if not bank_account.isalnum():
            return _("The IBAN number must contain only letters and digits")

        if not bank_account.startswith("RO"):
            return _("The IBAN number must start with 'RO'")

        return None

    @staticmethod
    @transaction.atomic
    def change_ngo_owner(ngo, new_ngo_owner):
        try:
            validate_email(new_ngo_owner)
        except ValidationError:
            return {"error": "Invalid email"}

        user_model = get_user_model()
        try:
            new_owner = user_model.objects.get(email=new_ngo_owner)
        except user_model.DoesNotExist:
            return {"error": "No user with this email"}

        if new_owner.ngo:
            return {"error": "This user already has an NGO"}

        old_user = user_model.objects.get(ngo=ngo)
        old_user.ngo = None
        new_owner.ngo = ngo

        old_user.save()
        new_owner.save()

        return {"success": "Owner changed successfully"}


class NgoRedirectionsView(ListView):
    template_name = "ngo-account/redirections/main.html"
    title = _("Redirections")
    context_object_name = "redirections"
    paginate_by = 8
    sidebar_item_target = "redirections"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "active_item": self.sidebar_item_target,
            }
        )

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


class NgoArchivesView(ListView):
    template_name = "ngo-account/archives/main.html"
    title = _("Archives history ")
    context_object_name = "archive_jobs"
    paginate_by = 8
    sidebar_item_target = "archives"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "active_item": self.sidebar_item_target,
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
