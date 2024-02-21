import logging

from django.core.management import BaseCommand
from django_q.tasks import schedule

from importer.tasks.logos import import_logos

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import NGO logos from the old storage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--schedule",
            action="store_true",
            help="Schedule the import for later",
        )

    def handle(self, *args, **options):
        should_schedule = options.get("schedule", False)

        if should_schedule:
            schedule(
                "importer.tasks.logos.import_logos",
                500,
                schedule_type="I",
                name="IMPORT_LOGOS",
                minutes=5,
                repeats=-1,
            )
            self.stdout.write(self.style.SUCCESS("NGO logo import scheduled"))
            return

        import_logos()

        self.stdout.write(self.style.SUCCESS("NGO logo import done"))
