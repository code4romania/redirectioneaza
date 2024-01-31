import csv
import logging
import operator
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone

from donations.models.main import Donor, Ngo
from .base import Handler


logger = logging.getLogger(__name__)


# TODO: The cron URLs should not be accessible by the public


class Stats(Handler):
    def get(self, request):
        now = timezone.now()
        start_of_year = datetime(now.year, 1, 1, 0, 0)
        # TODO: use aggregations for counting the totals in one step
        donations = Donor.objects.filter(date_created__gte=start_of_year).values("ngo_id", "has_signed")

        ngos = {}
        signed = 0
        for d in donations:
            ngos[d["ngo_id"]] = ngos.get(d["ngo_id"], 0)

            ngos[d["ngo_id"]] += 1

            if d["has_signed"]:
                signed += 1

        sorted_x = sorted(ngos.items(), key=operator.itemgetter(1))

        res = """
        Formulare semnate: {} <br>
        Top ngos: {}
        """.format(
            signed, sorted_x[len(sorted_x) - 10 :]
        )

        return HttpResponse(res)


class CustomExport(Handler):
    pass


class NgoExport(Handler):
    def get(self, request):
        fields = (
            "id",
            "name",
            "registration_number",
            "county",
            "active_region",
            "email",
            "website",
            "address",
        )

        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="ngo_export.csv"'},
        )

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(fields)

        for ngo in Ngo.objects.all().values(*fields):
            writer.writerow([ngo[field_name] for field_name in fields])

        return response


class NgoRemoveForms(Handler):
    def get(self, request):

        # get all the ngos
        ngos = Ngo.objects.all()

        logger.info("Removing form_url and custom_form from {0} ngos.".format(len(ngos)))

        # loop through them and remove the form_url
        # this will force an update on it when downloaded again
        for ngo in ngos:
            ngo.form_url = ""
            ngo.custom_form.delete()

        return HttpResponse("ok")
