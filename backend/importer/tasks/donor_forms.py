import logging
import tempfile

import requests
from django.core.files import File
from django.db.models import Q
from pypdf import PdfReader

from donations.models.main import Donor
from ..extract import DATA_ZONES, extract_data

logger = logging.getLogger(__name__)


def import_donor_forms(batch_size=50):
    """
    Download and re-upload the donation form files one by one
    """
    donor: Donor
    for donor in (
        Donor.objects.exclude(Q(pdf_url__isnull=True) | Q(pdf_url=""))
        .filter(Q(pdf_file="") | Q(pdf_file__isnull=True))
        .all()
        .order_by("-date_created")[:batch_size]
    ):
        logger.debug("Processing donation: %s", donor.first_name)

        if not donor.pdf_url.startswith("http"):
            logger.debug("Skipped form %s: PDF URL does not start with http", donor.first_name)
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

            address = {
                "street_name": extract_data(page, DATA_ZONES["street_name"]),
                "street_number": extract_data(page, DATA_ZONES["street_number"]),
                "bl": extract_data(page, DATA_ZONES["street_bl"]),
                "sc": extract_data(page, DATA_ZONES["street_sc"]),
                "et": extract_data(page, DATA_ZONES["street_et"]),
                "ap": extract_data(page, DATA_ZONES["street_ap"]),
            }
            donor.set_address(address)

            logger.debug("New form file: %s", donor.pdf_file)
            donor.save()
