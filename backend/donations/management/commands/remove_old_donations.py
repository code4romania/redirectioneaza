import datetime
import logging
from typing import Dict

from django.core.management import BaseCommand
from django.db.models import QuerySet
from django.utils import timezone

from donations.models.main import Donor
from redirectioneaza import settings

logger = logging.getLogger(__name__)


def age_unit_choices_converter(age_unit: str, age: int) -> Dict[str, int]:
    """
    Convert the age unit and age to a dictionary of days since timedelta doesn't support larger increments.
    Weeks can also work as a unit of time, but we choose to have only one unit of time for simplicity.
    Adding the hours, minutes, and seconds for testing purposes.

    :param age_unit: The unit of time to consider when converting.
    :param age: The amount of time to consider when converting.
    :return:
    """
    if age_unit == "days":
        return {"days": age}
    elif age_unit == "weeks":
        return {"days": age * 7}
    elif age_unit == "months":
        return {"days": age * 30}
    elif age_unit == "years":
        return {"days": age * 365}

    if settings.ENVIRONMENT == "production":
        raise ValueError("The provided environment does not support the provided age unit.")

    if age_unit == "hours":
        return {"hours": age}
    elif age_unit == "minutes":
        return {"minutes": age}
    elif age_unit == "seconds":
        return {"seconds": age}


class Command(BaseCommand):
    help = "Remove PII (encrypted or not) from old donations."

    default_age_unit = "years"
    default_age = 2

    blanked_string = "removed"
    queryset_batch_size = 100

    def add_arguments(self, parser):
        parser.add_argument(
            "--age_unit",
            type=str,
            help="The unit of time to consider when removing old donations.",
            choices=["years", "months", "weeks", "days", "hours", "minutes", "seconds"],
            default=self.default_age_unit,
            required=False,
        )
        parser.add_argument(
            "--age",
            type=int,
            help="The amount of time to consider when removing old donations.",
            default=self.default_age,
            required=False,
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the command in dry-run mode.",
        )
        parser.add_argument(
            "--run",
            action="store_true",
            help="Run the command instead of scheduling it.",
        )

    def _remove_data_from_queryset(self, donations: QuerySet[Donor], is_dry_run: bool) -> None:
        if not is_dry_run:
            donations.update(
                l_name=self.blanked_string,
                f_name=self.blanked_string,
                initial=self.blanked_string,
                encrypted_cnp="",
                encrypted_address="",
                phone="",
                email="",
                income_type="",
            )

            # remove the files from storage and the database
            for donation in donations:
                if donation.pdf_file:
                    donation.pdf_file.delete()
                    donation.pdf_file = None
                    donation.save()

        logger.info(f"Removed PII from {donations.count()} donations.")

    def process_data(self, age_unit, age_value, is_dry_run):
        now = timezone.now()
        default_time_delta = datetime.timedelta(**age_unit_choices_converter(self.default_age_unit, self.default_age))
        requested_time_delta = datetime.timedelta(**age_unit_choices_converter(age_unit, age_value))
        if default_time_delta != requested_time_delta and settings.ENVIRONMENT == "production":
            is_dry_run = True
        else:
            is_dry_run = is_dry_run
        donations_queryset = Donor.objects.filter(
            created_at__lt=(now - requested_time_delta),
        ).exclude(
            l_name=self.blanked_string,
            f_name=self.blanked_string,
            initial=self.blanked_string,
        )
        if donations_queryset.exists():
            for i in range(0, donations_queryset.count(), self.queryset_batch_size):
                self._remove_data_from_queryset(
                    donations=donations_queryset[i : i + self.queryset_batch_size],
                    is_dry_run=is_dry_run,
                )

    def handle(self, *args, **options):
        age_value = options["age"]
        age_unit = options["age_unit"]
        is_dry_run = options["dry_run"]

        self.process_data(age_unit, age_value, is_dry_run)

        logger.info("Finished removing old donations.")
