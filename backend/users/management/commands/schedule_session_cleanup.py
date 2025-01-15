import logging

from django.core.management import BaseCommand
from django.db.models import QuerySet
from django_q.models import Schedule
from django_q.tasks import schedule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Schedule a session cleanup task to run every day at 5:30 AM."
    schedule_name = "CLEANUP_SESSIONS"

    def handle(self, *args, **kwargs):
        logger.info("Scheduling session cleanup")

        self.remove_existing_schedules()
        self.schedule_session_cleanup()

        logger.info("Session cleanup scheduled successfully")

    def remove_existing_schedules(self):
        existing_schedules: QuerySet[Schedule] = Schedule.objects.filter(name=self.schedule_name)

        if not existing_schedules.exists():
            return

        logger.info(f"Removing {existing_schedules.count()} existing schedules")

        existing_schedules.delete()

    def schedule_session_cleanup(self):
        schedule(
            "django.core.management.call_command",
            "clearsessions",
            name=self.schedule_name,
            schedule_type=Schedule.DAILY,
            repeats=-1,
        )
