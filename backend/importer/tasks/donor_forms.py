import logging
from typing import List

from django.db.models import Count, Q, QuerySet
from django_q.tasks import async_task

from donations.models.donors import Donor
from donations.models.ngos import Ngo

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
        donor_forms_for_ngo: List[int] = Donor.objects.filter(
            ngo=ngo, pdf_file="", date_created__gte="2023-12-31"
        ).values_list("pk", flat=True)[: batch_size + 1]

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
    XXX: Will be removed
    """
    ...
