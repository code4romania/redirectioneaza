import logging

from django_q.models import Schedule
from django_q.tasks import schedule
from django.core.management import BaseCommand
from django.db.models import QuerySet
from django.utils import timezone

from q_heartbeat.management.commands.qheartbeat import SCHEDULE_NAME


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Schedule a heartbeat task to run every 10 minutes"

    def handle(self, *args, **kwargs):
        logger.info("Scheduling the task queue heartbeat")

        self.remove_existing_schedules()
        self.schedule_qheartbeat()

        logger.info("Task queue heartbeat scheduled successfully")

    def remove_existing_schedules(self):
        existing_schedules: QuerySet[Schedule] = Schedule.objects.filter(name=SCHEDULE_NAME)

        if not existing_schedules.exists():
            return

        logger.info(f"Removing {existing_schedules.count()} existing schedules")

        existing_schedules.delete()

    def schedule_qheartbeat(self):
        schedule(
            "django.core.management.call_command",
            "qheartbeat",
            name=SCHEDULE_NAME,
            schedule_type=Schedule.MINUTES,
            minutes=10,
            repeats=-1,
            next_run=timezone.now() + timezone.timedelta(minutes=0),
        )
