import logging
import tempfile

import requests
from django.core.files import File
from django.db.models import Q, QuerySet
from pypdf import PdfReader

from donations.models.main import Donor, Ngo
from ..extract import DATA_ZONES, extract_data

logger = logging.getLogger(__name__)


def import_donor_forms(batch_size=50, filter_by_ngo_slug: str = None):
    """
    Download and re-upload the donation form files one by one
    """
    donations_query: QuerySet[Donor] = (
        Donor.objects.exclude(Q(pdf_url__isnull=True) | Q(pdf_url=""))
        .filter(Q(pdf_file="") | Q(pdf_file__isnull=True))
        .all()
        .order_by("-date_created")
    )

    if filter_by_ngo_slug:
        target_ngo: Ngo = Ngo.objects.get(slug=filter_by_ngo_slug)

        donations_query = donations_query.filter(ngo=target_ngo)

    donor: Donor
    for donor in donations_query[:batch_size]:
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

            donor.set_address_helper(
                street_name=extract_data(page, DATA_ZONES["street_name"]),
                street_number=extract_data(page, DATA_ZONES["street_number"]),
                street_bl=extract_data(page, DATA_ZONES["street_bl"]),
                street_sc=extract_data(page, DATA_ZONES["street_sc"]),
                street_et=extract_data(page, DATA_ZONES["street_et"]),
                street_ap=extract_data(page, DATA_ZONES["street_ap"]),
            )

            logger.debug("New form file: %s", donor.pdf_file)
            donor.save()
