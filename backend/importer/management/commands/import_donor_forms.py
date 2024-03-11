import logging

from django.core.management import BaseCommand
from django_q.models import Schedule

from importer.tasks.donor_forms import import_donor_forms_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import donor forms from the old storage"

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

        kwargs = {"batch_size": batch_size, "run_async": True}

        if should_schedule:
            Schedule.objects.create(
                func=f"{import_donor_forms_task.__module__}.{import_donor_forms_task.__name__}",
                kwargs=kwargs,
                schedule_type=Schedule.MINUTES,
                minutes=5,
                name="CREATE_DONOR_FORMS_IMPORT_TASKS",
            )
            self.stdout.write(self.style.SUCCESS("Donor forms import scheduled"))
        else:
            kwargs["run_async"] = False

            import_donor_forms_task(**kwargs)

        self.stdout.write(self.style.SUCCESS("Donor forms import done"))
