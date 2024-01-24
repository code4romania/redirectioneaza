import logging
from copy import deepcopy
from datetime import datetime
from django.conf import settings
from django.core.exceptions import PermissionDenied, BadRequest
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from users.models import User
from .base import BaseHandler
from ..models import Ngo, Donor


logger = logging.getLogger(__name__)

# dict used as cache
stats_dict = {"init": False, "ngos": 0, "forms": 0, "years": {}, "counties": {}}


class AdminHome(BaseHandler):
    template_name = "admin2/index.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.is_staff:
            return redirect(User.create_admin_login_url(reverse("admin-index")))

        context["title"] = "Admin"
        now = timezone.now()

        ngos = []
        donations = []
        from_date = datetime(now.year, 1, 1, 0, 0)

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

            self.add_data(stats_dict, ngos, donations)

            stats_dict["init"] = True

        # just look at the last year
        ngos = Ngo.objects.filter(date_created__gte=from_date).all()
        donations = Donor.objects.filter(date_created__gte=from_date).all()

        stats = deepcopy(stats_dict)
        stats["ngos"] = len(ngos) + stats_dict["ngos"]
        stats["forms"] = len(donations) + stats_dict["forms"]

        self.add_data(stats, ngos, donations)

        context["stats_dict"] = stats

        # render a response
        return render(request, self.template_name, context)

    def add_data(self, obj, ngos, donations):
        for ngo in ngos:
            if ngo.date_created.year in obj["years"]:
                obj["years"][ngo.date_created.year]["ngos"] += 1

            if ngo.county:
                obj["counties"][ngo.county]["ngos"] += 1

        for donation in donations:
            if donation.date_created.year in obj["years"]:
                obj["years"][donation.date_created.year]["forms"] += 1

            obj["counties"][donation.county]["forms"] += 1


class AdminNewNgoHandler(BaseHandler):
    template_name = "admin2/ngo.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.is_staff:
            return redirect(User.create_admin_login_url(reverse("admin-ong-nou")))

        context["ngo_upload_url"] = reverse("api-ngo-upload-url")
        context["check_ngo_url"] = "/api/ngo/check-url/"
        context["counties"] = settings.LIST_OF_COUNTIES

        context["ngo"] = {}

        # render a response
        return render(request, self.template_name, context)


class AdminNgoHandler(BaseHandler):
    template_name = "admin2/ngo.html"

    def get(self, request, ngo_url, *args, **kwargs):
        context = {}

        if not request.user.is_staff:
            return redirect(User.create_admin_login_url(reverse("admin-ong")))

        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            return Http404

        context["ngo_upload_url"] = reverse("api-ngo-upload-url")
        context["counties"] = settings.LIST_OF_COUNTIES
        context["ngo"] = ngo

        try:
            context["owner"] = ngo.users.get()
        except User.DoesNotExist:
            context["owner"] = None

        context["other_emails"] = ", ".join(str(x) for x in ngo.other_emails) if ngo.other_emails else ""

        # render a response
        return render(request, self.template_name, context)


class AdminNgosList(BaseHandler):
    template_name = "admin2/ngos.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.is_staff:
            return redirect(User.create_admin_login_url(reverse("admin-ong")))

        context["title"] = "Admin"
        ngos = Ngo.objects.all()
        context["ngos"] = ngos

        # render a response
        return render(request, self.template_name, context)


class SendCampaign(BaseHandler):
    template_name = "admin2/campaign.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.is_staff:
            return redirect(User.create_admin_login_url(reverse("admin-campanii")))

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()

        subject = request.POST.get("subiect")
        emails = [s.strip() for s in request.POST.get("emails", "").split(",")]

        if not subject or not emails:
            raise BadRequest()

        sender_address = "Andrei Onel <contact@donezsi.eu>"

        html_template = "email/campaigns/first/index-inline.html"
        txt_template = "email/campaigns/first/index-text.txt"

        template_values = {}

        html_body = render_to_string(html_template, template_values)
        body = render_to_string(txt_template, template_values)

        for email in emails:
            user_address = email
            send_mail(
                from_email=sender_address,
                recipient_list=[user_address],
                subject=subject,
                html_message=html_body,
                message=body,
            )

        return redirect(reverse("admin-campanii"))


class UserAccounts(BaseHandler):
    template_name = "admin2/accounts.html"

    def get(self, request, *args, **kwargs):
        context = {}

        if not request.user.is_staff:
            return redirect(User.create_admin_login_url(reverse("admin-ong")))

        all_users = User.objects.order_by("-date_joined").all()
        context["users"] = all_users

        return render(request, self.template_name, context)
