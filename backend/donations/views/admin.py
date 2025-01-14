import logging

from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from redirectioneaza.common.cache import cache_decorator
from redirectioneaza.common.messaging import send_email
from users.models import User

from ..models.donors import Donor
from ..models.ngos import Ngo

logger = logging.getLogger(__name__)

# dict used as cache
stats_dict = {"init": False, "years": {}, "counties": {}, "all_time": {}}


class AdminHome(TemplateView):
    template_name = "admin2/index.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("admin-index")))

        context["title"] = "Admin"
        context["stats_dict"] = self.collect_stats()

        # render a response
        return render(request, self.template_name, context)

    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key="ADMIN_STATS")
    def collect_stats(self):
        return {
            "timestamp": timezone.now(),
            "years": self.get_yearly_data(),
            "counties": self.get_counties_data(),
            "all_time": self.get_all_time_data(),
        }

    @staticmethod
    def get_all_time_data():
        return {
            "ngos": Ngo.objects.all().count(),
            "forms": Donor.objects.all().count(),
            "ngos_with_forms": Donor.objects.all().values("ngo").distinct().count(),
        }

    @staticmethod
    def get_yearly_data():
        ngos_by_year = {
            year_stats["date_created__year"]: year_stats["count"]
            for year_stats in Ngo.active.values("date_created__year").annotate(count=Count("id"))
        }
        donations_by_year = {
            year_stats["date_created__year"]: year_stats["count"]
            for year_stats in Donor.objects.values("date_created__year").annotate(count=Count("id"))
        }
        ngos_donated_to_by_year = {
            year_stats["date_created__year"]: year_stats["count"]
            for year_stats in Donor.objects.values("date_created__year").annotate(count=Count("ngo", distinct=True))
        }

        return {
            year: {
                "ngos": ngos_by_year.get(year, 0),
                "forms": donations_by_year.get(year, 0),
                "ngos_donated_to_by_year": ngos_donated_to_by_year.get(year, 0) or 0,
            }
            for year in range(settings.START_YEAR, timezone.now().year + 1)
        }

    @staticmethod
    def get_counties_data():
        ngos_by_county = {
            county_stats["county"]: county_stats["count"]
            for county_stats in Ngo.active.values("county").annotate(count=Count("id"))
        }
        donations_by_county = {
            county_stats["county"]: county_stats["count"]
            for county_stats in Donor.objects.values("county").annotate(count=Count("id"))
        }
        donations_by_county_current_year = {
            county_stats["county"]: county_stats["count"]
            for county_stats in Donor.objects.filter(date_created__year=timezone.now().year)
            .values("county")
            .annotate(count=Count("id"))
        }
        return {
            county: {
                "ngos": ngos_by_county.get(county, 0),
                "forms": donations_by_county.get(county, 0),
                "forms_current_year": donations_by_county_current_year.get(county, 0),
            }
            for county in settings.LIST_OF_COUNTIES + ["1", "2", "3", "4", "5", "6", "RO"]
        }


class AdminNewNgoHandler(TemplateView):
    template_name = "admin2/ngo.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("admin-ong-nou")))

        context["ngo_upload_url"] = reverse("api-ngo-upload-url")
        context["check_ngo_url"] = "/api/ngo/check-url/"
        context["counties"] = settings.LIST_OF_COUNTIES

        context["ngo"] = {}

        # render a response
        return render(request, self.template_name, context)


class AdminNgoHandler(TemplateView):
    template_name = "admin2/ngo.html"

    def get(self, request, ngo_url, *args, **kwargs):
        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("login")))

        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            raise Http404

        context = {
            "ngo_upload_url": reverse("api-ngo-upload-url"),
            "counties": settings.FORM_COUNTIES_NATIONAL,
            "ngo": ngo,
        }

        try:
            context["owner"] = ngo.users.get()
        except User.DoesNotExist:
            context["owner"] = None

        # render a response
        return render(request, self.template_name, context)


class AdminNgosList(TemplateView):
    template_name = "admin2/ngos.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("admin-ngos")))

        context["title"] = "Admin"
        context["ngos"] = self._get_ngos()

        # render a response
        return render(request, self.template_name, context)

    def _get_ngos(self):
        return Ngo.objects.all().annotate(forms_count=Count("donor"))


class AdminNgosListByDate(AdminNgosList):
    def _get_ngos(self):
        return super()._get_ngos().order_by("-date_created")


class AdminNgosListByName(AdminNgosList):
    def _get_ngos(self):
        return super()._get_ngos().order_by("name")


class AdminNgosListByForms(AdminNgosList):
    def _get_ngos(self):
        return super()._get_ngos().order_by("-forms_count")


class AdminNgosListByFormsNow(AdminNgosList):
    def _get_ngos(self):
        query = (
            Ngo.objects.all()
            .annotate(
                forms_count=Count(
                    "donor",
                    filter=Q(
                        donor__date_created__year__gte=timezone.now().year,
                    ),
                )
            )
            .order_by("-forms_count")
        )
        return query


class AdminNgosListByFormsPrevious(AdminNgosList):
    def _get_ngos(self):
        query = (
            Ngo.objects.all()
            .annotate(
                forms_count=Count(
                    "donor",
                    filter=Q(
                        donor__date_created__year__gte=timezone.now().year - 1,
                        donor__date_created__year__lt=timezone.now().year,
                    ),
                )
            )
            .order_by("-forms_count")
        )
        return query


class SendCampaign(TemplateView):
    template_name = "admin2/campaign.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("admin-campanii")))

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("users.can_view_old_dashboard"):
            raise PermissionDenied()

        subject = request.POST.get("subiect")
        emails = [s.strip() for s in request.POST.get("emails", "").split(",")]

        if not subject or not emails:
            raise BadRequest()

        html_template = "email/campaigns/first/index-inline.html"
        txt_template = "email/campaigns/first/index-text.txt"

        send_email(
            subject=subject,
            to_emails=emails,
            text_template=txt_template,
            html_template=html_template,
            context={},
        )

        return redirect(reverse("admin-campanii"))


class UserAccounts(TemplateView):
    template_name = "admin2/accounts.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("admin-ong")))

        all_users = User.objects.order_by("-date_joined").all()
        context["users"] = all_users

        return render(request, self.template_name, context)
