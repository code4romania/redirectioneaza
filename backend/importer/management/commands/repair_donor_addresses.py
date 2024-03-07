import logging

from django.core.management import BaseCommand
from django_q.models import Schedule
from django_q.tasks import schedule

from importer.tasks.repair_addresses import repair_addresses_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Repair the addresses of donors that were saved with the wrong format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--schedule",
            action="store_true",
            help="Schedule the import for later",
        )
        parser.add_argument(
            "--batch_size",
            type=int,
            help="The number of donors to process in a single task",
            required=False,
            default=1000,
        )

    def handle(self, *args, **options):
        should_schedule = options.get("schedule", False)
        batch_size = options.get("batch_size")

        if should_schedule:
            schedule(
                "importer.tasks.repair_addresses.repair_addresses_task",
                batch_size,
                schedule_type=Schedule.ONCE,
                name="CREATE_ADDRESS_REPAIR_TASKS",
            )
            self.stdout.write(self.style.SUCCESS("Address repair task scheduled"))
            return

        repair_addresses_task(batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS("Address repair task done!"))
