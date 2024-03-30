import logging
from copy import deepcopy
from datetime import datetime

from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models import Count
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from redirectioneaza.common.messaging import send_email
from users.models import User
from ..models.main import Donor, Ngo

logger = logging.getLogger(__name__)

# dict used as cache
stats_dict = {"init": False, "ngos": 0, "forms": 0, "years": {}, "counties": {}}


class AdminHome(TemplateView):
    template_name = "admin2/index.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.has_perm("users.can_view_old_dashboard"):
            return redirect(User.create_admin_login_url(reverse("admin-index")))

        context["title"] = "Admin"
        now = timezone.now()

        from_date = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)

        # if we don't have any data
        if stats_dict["init"] is False:
            ngos = []
            donations = []

            stats_dict["ngos"] = len(ngos)
            stats_dict["forms"] = len(donations)

            # init the rest of the dict
            for x in range(settings.START_YEAR, now.year + 1):
                stats_dict["years"][x] = {
                    "ngos": 0,
                    "forms": 0,
                }

            counties = settings.LIST_OF_COUNTIES + ["1", "2", "3", "4", "5", "6", "RO"]

            for county in counties:
                stats_dict["counties"][county] = {
                    "ngos": 0,
                    "forms": 0,
                }

            self.add_data(stats_dict)

            stats_dict["init"] = True

        # just look at the last year
        ngos = Ngo.objects.filter(date_created__gte=from_date).all()
        donations = Donor.objects.filter(date_created__gte=from_date).all()

        stats = deepcopy(stats_dict)
        stats["ngos"] = ngos.count() + stats_dict["ngos"]
        stats["forms"] = donations.count() + stats_dict["forms"]

        self.add_data(stats)

        context["stats_dict"] = stats

        # render a response
        return render(request, self.template_name, context)

    def add_data(self, obj):
        ngos_by_year = {
            year_stas["date_created__year"]: year_stas["count"]
            for year_stas in Ngo.active.values("date_created__year").annotate(count=Count("id"))
        }
        donations_by_year = {
            year_stas["date_created__year"]: year_stas["count"]
            for year_stas in Donor.objects.values("date_created__year").annotate(count=Count("id"))
        }

        ngos_by_county = {
            county_stats["county"]: county_stats["count"]
            for county_stats in Ngo.active.values("county").annotate(count=Count("id"))
        }
        donations_by_county = {
            county_stats["county"]: county_stats["count"]
            for county_stats in Donor.objects.values("county").annotate(count=Count("id"))
        }

        obj["years"] = {
            year: {"ngos": ngos_by_year.get(year, 0), "forms": donations_by_year.get(year, 0)}
            for year in range(settings.START_YEAR, timezone.now().year + 1)
        }
        obj["counties"] = {
            county: {"ngos": ngos_by_county.get(county, 0), "forms": donations_by_county.get(county, 0)}
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
            "other_emails": ", ".join(str(x) for x in ngo.other_emails) if ngo.other_emails else "",
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
        ngos = Ngo.objects.all()
        context["ngos"] = ngos

        # render a response
        return render(request, self.template_name, context)


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
