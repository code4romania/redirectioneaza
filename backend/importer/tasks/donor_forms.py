import logging
import tempfile
from typing import List

import requests
from django.core.files import File
from django.db.models import Count, Q, QuerySet
from django_q.tasks import async_task
from pypdf import PdfReader
from requests import Response

from donations.models.main import Donor, Ngo
from ..extract import DATA_ZONES, extract_data

logger = logging.getLogger(__name__)


def import_donor_forms_task(batch_size: int = 50):
    logger.info("Starting a new donor form import task")

    ngos_by_number_of_donors: QuerySet[Ngo] = (
        Ngo.objects.all()
        .annotate(
            number_of_donors=Count(
                "donor",
                filter=(
                    ~Q(donor__pdf_url="")
                    & Q(donor__pdf_file="")
                    & Q(donor__has_signed=True)
                    & Q(donor__date_created__gte="2022-12-31")
                ),
            )
        )
        .exclude(Q(number_of_donors=0) | Q(number_of_donors__gt=batch_size * 2))
    )

    logger.info("Found %d NGOs with donors", ngos_by_number_of_donors.count())

    processed_forms: List[int] = []
    for index, ngo in enumerate(ngos_by_number_of_donors):
        donor_forms_for_ngo: List[int] = (
            Donor.objects.filter(ngo=ngo, pdf_file="", has_signed=True, date_created__gte="2022-12-31")
            .exclude(pdf_url="")
            .values_list("pk", flat=True)[: batch_size + 1]
        )

        processed_forms.extend(donor_forms_for_ngo)

        if len(processed_forms) > batch_size:
            logger.info("Scheduling a new task for %d donors from %d NGOs", len(processed_forms), index + 1)

            async_task(import_donor_forms, processed_forms)
            break

    return


def import_donor_forms(ids: List[int]):
    """
    Download and re-upload the donation form files one by one
    """
    target_donors: QuerySet[Donor] = Donor.objects.filter(pk__in=ids).order_by("pk")

    logger.info("Found %s donors to import", target_donors.count())

    donor: Donor
    for donor in target_donors:
        logger.debug("Processing donation: %s", donor.first_name)

        if not donor.pdf_url.startswith("http"):
            logger.debug("Skipped form %s: PDF URL does not start with http", donor.first_name)
            continue

        r: Response = requests.get(donor.pdf_url)
        if r.status_code != 200:
            logger.debug("Donation form request status: %s", r.status_code)
            continue

        with tempfile.TemporaryFile() as fp:
            fp.write(r.content)
            fp.seek(0)
            donor.pdf_file.save("donation_form.pdf", File(fp), save=False)
            fp.seek(0)
            reader = PdfReader(fp)
            page = reader.pages[0]

            try:
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
            except Exception as e:
                logger.error("Error extracting data from PDF: %s for donor %s", e, donor.pk)
                continue

            logger.debug("New form file: %s", donor.pdf_file)

            donor.save()
