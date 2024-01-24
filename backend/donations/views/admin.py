import logging
from copy import deepcopy
from datetime import datetime
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect, render
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
    pass


class AdminNgoHandler(BaseHandler):
    pass


class AdminNgosList(BaseHandler):
    pass


class SendCampaign(BaseHandler):
    pass


class UserAccounts(BaseHandler):
    pass
