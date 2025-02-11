import logging

import psutil
from django_q.models import Schedule, Success
from django.core.management.base import BaseCommand
from django.utils import timezone


logger = logging.getLogger(__name__)

SCHEDULE_NAME = "QHEARTBEAT"


class Command(BaseCommand):
    help = "Without args, this command is a no-op just for registering that the task queue is alive"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hard",
            action="store_true",
            default=False,
            help="Kill the worker processes instead of terminating them",
        )
        parser.add_argument(
            "--check-minutes",  # this will be stored in options["check_minutes"]
            type=int,
            default=0,
            help="Check for at least one successful task in the past N minutes",
        )

    def handle(self, *args, **options):
        check_minutes = options.get("check_minutes", 0)

        # Do we have to check for past heartbeats, or just mark a new one?
        if not check_minutes:
            logger.info("Just a task queue heartbeat")
            return

        # If there is no heartbeat schedule set up, then there is nothing to check
        if not Schedule.objects.filter(name=SCHEDULE_NAME).exists():
            logger.info("Did not check for queue heartbeat because there is no heartbeat schedule")
            return

        # Check if there were any successful tasks started in the past N minutes
        cutoff = timezone.now() - timezone.timedelta(minutes=check_minutes)
        if not Success.objects.filter(started__gte=cutoff).exists():
            # If there are no successful tasks, then try to terminate the workers
            logger.error("The task queue seems to be stuck, attempting to terminate it")
            self.terminate_workers(options.get("hard", False))
        else:
            logger.info("The task queue seems to be working")

    def terminate_workers(self, hard_attempt: False) -> None:
        """
        Terminate or kill all cluster workers
        """
        needle_name = "python3"
        needle_cmd = [needle_name, "manage.py", "qcluster"]
        worker_count = 0
        for proc in psutil.process_iter():
            if proc.name() == needle_name and proc.cmdline() == needle_cmd:
                worker_count += 1
                proc.kill() if hard_attempt else proc.terminate()
        logging.warning("%s %d qcluster workers", "Killed" if hard_attempt else "Terminated", worker_count)
