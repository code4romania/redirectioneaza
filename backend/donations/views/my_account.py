from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator

from redirectioneaza.common.cache import cache_decorator
from users.models import User
from .base import AccountHandler
from ..models.jobs import Job, JobStatusChoices
from ..models.main import Donor, Ngo


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

        if user.is_superuser:
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
    @cache_decorator(cache_key_prefix="DONORS_BY_DONATION_YEAR", timeout=settings.CACHE_TIMEOUT_TINY)
    def _get_donors_by_donation_year(ngo: Ngo) -> OrderedDict:
        donors_grouped_by_year = OrderedDict()

        count_per_year = {}
        for donor in Donor.objects.filter(ngo=ngo).order_by("-date_created"):
            donation_year = donor.date_created.year
            if count_per_year.get(donation_year, 0) > 10:
                continue
            if donation_year not in donors_grouped_by_year:
                count_per_year[donation_year] = 0
                donors_grouped_by_year[donation_year] = []
            donors_grouped_by_year[donation_year].append(donor)
            count_per_year[donation_year] += 1

        return donors_grouped_by_year

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request: HttpRequest, *args, **kwargs):
        user: User = request.user

        if user.is_superuser:
            return redirect(reverse("admin-ngos"))

        user_ngo: Ngo = user.ngo if user.ngo else None

        grouped_donors = self._get_donors_by_donation_year(ngo=user_ngo)

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
            "counties": settings.FORM_COUNTIES_NATIONAL,
            "disable_download": disable_download,
            "has_signed_form": has_signed_form,
            "current_year": now.year,
            "ngo_url": ngo_url,
            "DEFAULT_NGO_LOGO": settings.DEFAULT_NGO_LOGO,
        }

        return render(request, self.template_name, context)


class NgoDetailsHandler(AccountHandler):
    template_name = "ngo/ngo-details.html"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_superuser:
            return redirect(reverse("admin-ngos"))

        if not user.is_authenticated or not user.ngo:
            return redirect(reverse("contul-meu"))

        context = {
            "title": "Date asociație",
            "user": user,
            "ngo": user.ngo if user.ngo else None,
            "counties": settings.FORM_COUNTIES_NATIONAL,
            "DEFAULT_NGO_LOGO": settings.DEFAULT_NGO_LOGO,
        }

        return render(request, self.template_name, context)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied()

        if user.is_superuser:
            ngo_url = post.get("old-ong-url", "")

            try:
                user.ngo = Ngo.objects.get(slug=ngo_url)
            except Ngo.DoesNotExist:
                raise Http404()

        ngo: Ngo = user.ngo

        is_new_ngo = False
        if not ngo:
            is_new_ngo = True

            ngo = Ngo()

            ngo.is_verified = False
            ngo.is_active = True

        ngo.name = post.get("ong-nume")
        ngo.description = post.get("ong-descriere")
        ngo.phone = post.get("ong-tel")
        ngo.email = post.get("ong-email")
        ngo.website = post.get("ong-website")
        ngo.address = post.get("ong-adresa")
        ngo.county = post.get("ong-judet")
        ngo.active_region = post.get("ong-activitate")
        ngo.slug = post.get("ong-url").lower()
        ngo.registration_number = post.get("ong-cif")
        ngo.bank_account = post.get("ong-cont")
        ngo.has_special_status = True if post.get("special-status") == "on" else False
        ngo.is_accepting_forms = True if post.get("accepts-forms") == "on" else False

        ngo.other_emails = ""

        if request.user.is_superuser:
            ngo.is_verified = post.get("ong-verificat") == "on"
            ngo.is_active = post.get("ong-activ") == "on"

        if new_ngo_owner := post.get("new-ngo-owner"):
            change_owner_result = self.change_ngo_owner(ngo, new_ngo_owner)

            if "error" in change_owner_result:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))

        ngo.save()

        if is_new_ngo:
            user.ngo = ngo
            user.save()
            if request.user.is_superuser:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))
            else:
                return redirect(reverse("contul-meu"))

        else:
            if request.user.is_superuser:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))
            else:
                return redirect(reverse("association"))

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
