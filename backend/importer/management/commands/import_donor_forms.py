import logging
import requests
import tempfile

from pypdf import PdfReader
from django.db.models import Q
from django.core.files import File
from django.core.management import BaseCommand

from donations.models.main import Donor

from ...extract import DATA_ZONES, extract_data


logger = logging.getLogger(__name__)


def _import_donor_forms(batch_size=50):
    """
    Download an reupload the donation form files one by one
    """
    for donor in (
        Donor.objects.exclude(Q(pdf_url__isnull=True) | Q(pdf_url=""))
        .filter(Q(pdf_file="") | Q(pdf_file__isnull=True))
        .all()
        .order_by("-date_created")[:batch_size]
    ):
        logger.debug("Processing donation: %s", donor.name)

        if not donor.pdf_url.startswith("http"):
            logger.debug("Skipped form %s: PDF URL does not start with http", donor.name)
            continue

        r = requests.get(donor.pdf_url)
        if r.status_code != 200:
            logger.debug("Donation form request status: %s", r.status_code)

        with tempfile.TemporaryFile() as fp:
            fp.write(r.content)
            fp.seek(0)
            donor.pdf_file.save("donation_form.pdf", File(fp))
            fp.seek(0)
            reader = PdfReader(fp)
            page = reader.pages[0]

            donor.set_cnp(extract_data(page, DATA_ZONES["cnp"]))
            donor.initial = extract_data(page, DATA_ZONES["father"])

            # print("Street Name =", extract_data(page, DATA_ZONES["street_name"]))
            # print("Street Number =", extract_data(page, DATA_ZONES["street_number"]))
            # print("BL =", extract_data(page, DATA_ZONES["street_bl"]))
            # print("SC =", extract_data(page, DATA_ZONES["street_sc"]))
            # print("ET =", extract_data(page, DATA_ZONES["street_et"]))
            # print("AP =", extract_data(page, DATA_ZONES["street_ap"]))
            # print("Percent =", extract_data(page, DATA_ZONES["percent"]))

            logger.debug("New form file: %s", donor.pdf_file)
            donor.save()


class Command(BaseCommand):
    help = "Import donor forms from the old storage"

    def handle(self, *args, **options):
        _import_donor_forms()
        self.stdout.write(self.style.SUCCESS("Donor forms import done"))
