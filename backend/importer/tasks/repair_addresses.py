import ast
import logging
from json import JSONDecodeError

from django.conf import settings
from django.db.models import QuerySet

from donations.models.donors import Donor
from importer.tasks.utils import batch
from redirectioneaza.common.async_wrapper import async_wrapper

logger = logging.getLogger(__name__)


def repair_addresses_task(batch_size: int = 1000) -> None:
    target_donor_ids: QuerySet[int] = (
        Donor.objects.exclude(encrypted_address="").values_list("pk", flat=True).order_by("pk")
    )

    for donor_ids in batch(target_donor_ids, batch_size):
        logger.info("Starting task for the following list of donors: %s", len(donor_ids))
        async_wrapper(repair_address_batch, donor_ids)


def repair_address_batch(ids: list) -> None:
    target_donors: QuerySet[Donor] = Donor.available.filter(pk__in=ids).order_by("pk")

    logger.info("Found %s donors with addresses to repair", target_donors.count())

    for donor in target_donors:
        logger.debug("Processing donor %s", donor.pk)

        try:
            Donor.decrypt_address(donor.encrypted_address)
        except JSONDecodeError:
            repair_address(donor)
        else:
            continue


def repair_address(donor: Donor) -> None:
    logger.debug("Repairing address for donor %s", donor.pk)

    encrypted_address: str = donor.encrypted_address
    decoded_address: str = settings.FERNET_OBJECT.decrypt(encrypted_address.encode()).decode()

    try:
        decoded_address: dict = dict(ast.literal_eval(decoded_address))
    except ValueError:
        logger.error("Received a ValueError trying to convert address to dict for donor %s", donor.pk)
        return
    except SyntaxError:
        logger.error("Received a SyntaxError trying to convert address to dict for donor %s", donor.pk)
        return

    address_dict = {
        "street_name": decoded_address.get("str", ""),
        "street_number": decoded_address.get("nr", ""),
        "street_bl": decoded_address.get("bl", ""),
        "street_sc": decoded_address.get("sc", ""),
        "street_et": decoded_address.get("et", ""),
        "street_ap": decoded_address.get("ap", ""),
    }

    donor.set_address_helper(**address_dict)
    donor.save(update_fields=["encrypted_address"])
