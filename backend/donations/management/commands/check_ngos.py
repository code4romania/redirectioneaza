import logging
import time

import requests
from django.conf import settings
from django.core.management import BaseCommand

from donations.models.ngos import Ngo
from donations.workers.check_organization import cult_registry_check_organizations

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Check NGOs in ANAF Cult Registry"

    def check_endpoint_alive(self):
        try:
            requests.get(settings.ANAF_CULT_REGISTRY_ENDPOINT)
        except ConnectionError:
            return False
        else:
            return True

    def handle(self, *args, **options):
        if not settings.ENABLE_ANAF_CULT_REGISTRY:
            logger.info("ANAF Cult Registry checks are disabled")
            return

        if not self.check_endpoint_alive():
            # If the endpoint is down, there's no point in continuing with the checks
            self.stdout.write("ANAF endpoint is down. Ending the NGO Registry check task.")
            return
        else:
            # If the endpoint is up, pause for a bit in order to not break the endpoint request limit
            time.sleep(2)

        qs: list[str] = (
            Ngo.objects.exclude(pause_cult_registry_check=True)
            # check only NGOs whose registration number is valid:
            .filter(registration_number_valid=True)
            # check NGOs which are were not yet checked in the registry:
            .filter(is_in_cult_registry__isnull=True)
            .distinct("registration_number")
            .values_list("registration_number", flat=True)
        )
        registration_numbers: set[str] = set(qs[: settings.ANAF_CULT_REGISTRY_BATCH_SIZE])

        result = cult_registry_check_organizations(list(registration_numbers), "sync")

        self.stdout.write(
            f"Checked {len(registration_numbers)} NGOs in ANAF Cult Registry: "
            f"{result.get('present')} present, {result.get('absent')} absent, {result.get('error')} error"
        )
