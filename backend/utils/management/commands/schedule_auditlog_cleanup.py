import logging
from datetime import timedelta

from django.core.management import BaseCommand
from django.db.models import QuerySet
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import schedule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Schedule an expired auditlog cleanup task to run once a day"
    schedule_name = "CLEANUP_AUDITLOG"

    def handle(self, *args, **kwargs):
        logger.info("Scheduling auditlog cleanup")

        self.remove_existing_schedules()
        self.schedule_auditlog_cleanup()

        logger.info("Auditlog cleanup scheduled successfully")

    def remove_existing_schedules(self):
        existing_schedules: QuerySet[Schedule] = Schedule.objects.filter(name=self.schedule_name)

        if not existing_schedules.exists():
            return

        logger.info(f"Removing {existing_schedules.count()} existing schedules")

        existing_schedules.delete()

    def schedule_auditlog_cleanup(self):
        schedule(
            "django.core.management.call_command",
            "cleanup_auditlog",
            name=self.schedule_name,
            schedule_type=Schedule.DAILY,
            repeats=-1,
            next_run=timezone.now() + timedelta(minutes=7),
        )
