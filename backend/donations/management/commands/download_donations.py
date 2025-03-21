import logging
import time

from django.core.management import BaseCommand
from django_q.models import Schedule
from django_q.tasks import async_task

from donations.views.download_donations.main import download_donations_job

logger = logging.getLogger(__name__)

TASK_PREFIX = "DOWNLOAD-DONATIONS-TASK"


class Command(BaseCommand):
    help = "Generate the zip file with the donations for a given organization."

    def add_arguments(self, parser):
        parser.add_argument(
            "job_id",
            type=int,
            help="The ID of the organization to generate donations for",
        )
        parser.add_argument(
            "--run",
            action="store_true",
            help="Schedule projects assignment instead of running the script once.",
        )

    def handle(self, *args, **options):
        job_id: int = options["job_id"]

        if options["run"]:
            self.stdout.write(self.style.SUCCESS(f"Running download for job with ID #{job_id}."))

            success_message: str = f"ran download task for job with ID #{job_id}."
            start = time.time()

            download_donations_job(job_id)

            end = time.time()
            result = end - start

            logger.info(f"Download took {result} seconds.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Setting up download task for job with ID #{job_id}."))

            success_message: str = f"set up download task for job with ID #{job_id}."
            self._run_async(job_id)

        self.stdout.write(self.style.SUCCESS(f"Successfully {success_message}."))

    def _run_async(self, job_id: int):
        task_id = f"{TASK_PREFIX}-{str(job_id).zfill(8)}"

        try:
            Schedule.objects.get(name=task_id).delete()
            self.stdout.write(self.style.SUCCESS("Schedule already exists. Deleting and recreating."))
        except Schedule.MultipleObjectsReturned:
            Schedule.objects.filter(name=task_id).delete()
            self.stdout.write(self.style.ERROR("Multiple schedules found. Deleting and creating one."))
        except Schedule.DoesNotExist:
            pass

        async_task("donations.views.download_donations.main.download_donations_job", job_id)
