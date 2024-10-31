import logging
import tempfile
from typing import List

import requests
from django.conf import settings
from django.core.files import File
from django.db.models import Count, Q, QuerySet
from django_q.tasks import async_task
from pypdf import PdfReader
from requests import Response
from sentry_sdk import capture_message

from donations.models.main import Donor, Ngo

from ..extract import DATA_ZONES, extract_data

logger = logging.getLogger(__name__)


def import_donor_forms_task(batch_size: int = 50, run_async: bool = False, dry_run: bool = False):
    logger.info("Starting a new donor form import task")

    ngos_by_number_of_donors: QuerySet[Ngo] = (
        Ngo.objects.all()
        .annotate(
            number_of_donors=Count(
                "donor",
                filter=(~Q(donor__pdf_url="") & Q(donor__pdf_file="") & Q(donor__date_created__gte="2023-12-31")),
            )
        )
        .exclude(number_of_donors=0)
    )

    logger.info("Found %d NGOs with donors", ngos_by_number_of_donors.count())

    index: int = 0
    processed_form_ids: List[int] = []
    for index, ngo in enumerate(ngos_by_number_of_donors):
        donor_forms_for_ngo: List[int] = (
            Donor.objects.exclude(pdf_url="")
            .filter(ngo=ngo, pdf_file="", date_created__gte="2023-12-31")
            .values_list("pk", flat=True)[: batch_size + 1]
        )

        processed_form_ids.extend(donor_forms_for_ngo)

        if len(processed_form_ids) > batch_size:
            execute_import(index, processed_form_ids, run_async, dry_run)

            break
    else:
        if index:
            execute_import(index, processed_form_ids, run_async, dry_run)

    return


def execute_import(index, processed_form_ids: List[int], run_async: bool, dry_run):
    logger.info("Scheduling a new task for %d donors from %d NGOs", len(processed_form_ids), index + 1)

    if run_async:
        async_task(import_donor_forms, ids=processed_form_ids, dry_run=dry_run)
    else:
        import_donor_forms(processed_form_ids, dry_run)


def import_donor_forms(ids: List[int], dry_run: bool):
    """
    Download and re-upload the donation form files one by one
    """
    target_donors: QuerySet[Donor] = Donor.objects.filter(pk__in=ids).order_by("pk")

    logger.info("Found %s donors to import", target_donors.count())

    attempted_donors: int = 0
    transferred_donors: int = 0

    donor: Donor
    for attempted_donors, donor in enumerate(target_donors):

        logger.debug("Processing donation: %s", donor.pk)

        if not donor.pdf_url.startswith("http"):
            logger.debug("Skipped form %s: PDF URL does not start with http", donor.pk)
            continue

        r: Response = requests.get(donor.pdf_url)
        if r.status_code != 200:
            error_message = f"Donation form request status: {r.status_code} for donor {donor.pk}"
            logger.warning(error_message)

            if settings.ENABLE_SENTRY:
                capture_message(error_message, level="error")

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

            if not dry_run:
                donor.save()
            else:
                logger.info("Dry run: not saving the donor form")

            transferred_donors += 1

    if transferred_donors:
        logger.info("Transferred %d out of %d donors", transferred_donors, attempted_donors + 1)
    else:
        error_message = f"No donors were transferred for the following list of {attempted_donors + 1} IDs: {ids}"
        logger.error(error_message)

        if settings.ENABLE_SENTRY:
            capture_message(error_message, level="error")
