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
from django_q.tasks import async_task

from redirectioneaza.common.cache import cache_decorator
from users.models import User
from .api import CheckNgoUrl
from .base import AccountHandler
from ..models.jobs import Job, JobStatusChoices
from ..models.main import Donor, Ngo, ngo_id_number_validator


class MyAccountDetailsHandler(AccountHandler):
    template_name = "ngo/my-account-details.html"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        context = {"user": request.user}
        return render(request, self.template_name, context)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST

        request.user.last_name = post.get("nume")
        request.user.first_name = post.get("prenume")

        request.user.save()

        context = {"user": request.user}

        return render(request, self.template_name, context)


class ArchiveDownloadLinkHandler(AccountHandler):
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
            # Check that the asked job belongs to the current user
            try:
                job = Job.objects.get(pk=job_id, ngo=user.ngo, owner=user)
            except Job.DoesNotExist:
                raise Http404

        # Check that the job has a zip file
        if not job.zip:
            raise Http404

        return redirect(job.zip.url)


class MyAccountHandler(AccountHandler):
    template_name = "ngo/my-account.html"

    @staticmethod
    @cache_decorator(timeout=settings.CACHE_TIMEOUT_TINY, cache_key_prefix="DONORS_BY_DONATION_YEAR")
    def _get_donors_by_donation_year(ngo: Ngo) -> OrderedDict:
        donors_grouped_by_year = OrderedDict()

        count_per_year = {}
        for donor in Donor.objects.filter(ngo=ngo).order_by("-date_created"):
            donation_year = donor.date_created.year
            if donation_year not in donors_grouped_by_year:
                count_per_year[donation_year] = 0
                donors_grouped_by_year[donation_year] = []
            donors_grouped_by_year[donation_year].append(donor)
            count_per_year[donation_year] += 1

        return donors_grouped_by_year

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request: HttpRequest, *args, **kwargs):
        user: User = request.user

        if user.has_perm("users.can_view_old_dashboard"):
            return redirect(reverse("admin-ngos"))

        user_ngo: Ngo = user.ngo if user.ngo else None

        grouped_donors = self._get_donors_by_donation_year(ngo=user_ngo)
        donors_metadata = {
            "total": sum(len(donors) for donors in grouped_donors.values()),
            "total_signed": sum(1 for donors in grouped_donors.values() if donors),
            "years": list(grouped_donors.keys()),
        }

        now = timezone.now()
        can_donate = not now.date() > settings.DONATIONS_LIMIT

        ngo_url = (
            request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": user_ngo.slug})) if user_ngo else ""
        )

        ngo_jobs = user_ngo.jobs.all()[:10] if user_ngo else None

        last_job_was_recent = False
        if ngo_jobs:
            last_job_date = ngo_jobs[0].date_created
            last_job_status = ngo_jobs[0].status

            if last_job_status != JobStatusChoices.ERROR:
                timedelta = timezone.timedelta(hours=12)
            else:
                timedelta = timezone.timedelta(minutes=30)

            if last_job_date > now - timedelta:
                last_job_was_recent = True

        has_signed_form = user_ngo.is_accepting_forms if user_ngo else False
        disable_download = settings.ENABLE_FORMS_DOWNLOAD and (
            not has_signed_form or not can_donate or last_job_was_recent
        )

        context = {
            "user": user,
            "jobs": ngo_jobs,
            "limit": settings.DONATIONS_LIMIT,
            "ngo": user_ngo,
            "donors": grouped_donors,
            "donor_metadata": donors_metadata,
            "counties": settings.FORM_COUNTIES_NATIONAL,
            "disable_download": disable_download,
            "has_signed_form": has_signed_form,
            "current_year": now.year,
            "ngo_url": ngo_url,
        }

        return render(request, self.template_name, context)


def delete_prefilled_form(ngo_id):
    return Ngo.delete_prefilled_form(ngo_id)


class NgoDetailsHandler(AccountHandler):
    template_name = "ngo/ngo-details.html"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.has_perm("users.can_view_old_dashboard"):
            return redirect(reverse("admin-ngos"))

        if not user.is_authenticated or not user.ngo:
            return redirect(reverse("contul-meu"))

        context = {
            "title": "Date organizație",
            "user": user,
            "ngo": user.ngo if user.ngo else None,
            "counties": settings.FORM_COUNTIES_NATIONAL,
        }

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

        ngo: Ngo = user.ngo

        must_refresh_form = False
        is_new_ngo = False

        if not ngo:
            is_new_ngo = True

            ngo = Ngo()

            ngo.is_verified = False
            ngo.is_active = True

        registration_number = post.get("ong-cif", "").upper().replace(" ", "").replace("<", "").replace(">", "")[:20]
        registration_number_errors: str = self._validate_registration_number(ngo, registration_number)
        if ngo.registration_number != registration_number:
            ngo.registration_number = registration_number
            must_refresh_form = True

        bank_account = post.get("ong-cont", "").strip().upper().replace(" ", "").replace("<", "").replace(">", "")[:34]
        bank_account_errors: str = self._validate_iban_number(bank_account)
        if ngo.bank_account != bank_account:
            ngo.bank_account = bank_account
            must_refresh_form = True

        ngo_slug = post.get("ong-url", "").strip().lower()
        ngo_slug_errors = CheckNgoUrl.validate_ngo_slug(user, ngo_slug)
        ngo.slug = ngo_slug

        ngo_name = post.get("ong-nume", "").strip()
        if ngo.name != ngo_name:
            ngo.name = ngo_name
            must_refresh_form = True

        ngo.description = post.get("ong-descriere", "").strip()
        ngo.phone = post.get("ong-tel", "").strip()
        ngo.email = post.get("ong-email", "").strip()
        ngo.website = post.get("ong-website", "").strip()
        ngo.address = post.get("ong-adresa", "").strip()
        ngo.county = post.get("ong-judet", "").strip()
        ngo.active_region = post.get("ong-activitate", "").strip()
        ngo.has_special_status = True if post.get("special-status") == "on" else False
        ngo.is_accepting_forms = True if post.get("accepts-forms") == "on" else False

        errors: List[str] = []
        if registration_number_errors:
            errors.append(registration_number_errors)

        if bank_account_errors:
            errors.append(bank_account_errors)

        if isinstance(ngo_slug_errors, HttpResponseBadRequest):
            errors.append(_("The URL is already used"))

        if errors:
            context = {
                "title": "Date organizație",
                "user": user,
                "ngo": ngo,  # send back the unsaved NGO data
                "counties": settings.FORM_COUNTIES_NATIONAL,
                "errors": errors,
            }
            return render(request, self.template_name, context)

        ngo.other_emails = ""

        if request.user.has_perm("users.can_view_old_dashboard"):
            ngo.is_verified = post.get("ong-verificat") == "on"
            ngo.is_active = post.get("ong-activ") == "on"

        if new_ngo_owner := post.get("new-ngo-owner"):
            change_owner_result = self.change_ngo_owner(ngo, new_ngo_owner)

            if "error" in change_owner_result:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))

        ngo.save()

        # Delete the NGO's old prefilled form
        if must_refresh_form:
            async_task("donations.views.my_account.delete_prefilled_form", ngo.id)

        if is_new_ngo:
            user.ngo = ngo
            user.save()

        if request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))

        return redirect(reverse("organization"))

    @staticmethod
    def _validate_registration_number(ngo, registration_number) -> Optional[str]:
        try:
            ngo_id_number_validator(registration_number)
        except ValidationError:
            return f'CIF "{registration_number}" pare incorect'

        reg_num_query: QuerySet[Ngo] = Ngo.objects.filter(registration_number=registration_number)
        if ngo.pk:
            reg_num_query = reg_num_query.exclude(pk=ngo.pk)

        if reg_num_query.count():
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
