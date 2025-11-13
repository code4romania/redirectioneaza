import logging
from datetime import datetime

from django.core.management import BaseCommand
from django.db.models import QuerySet
from django_q.models import Schedule
from django_q.tasks import schedule

logger = logging.getLogger(__name__)


class SchedulerCommand(BaseCommand):
    function_name: str = "django.core.management.call_command"

    command_name: str
    function_args: tuple

    schedule_name: str
    schedule_details: dict[str, int | datetime]

    def handle(self, *args, **kwargs):
        logger.info("Scheduling the task")

        self.remove_existing_schedules()
        self.schedule_task()

        logger.info("Task scheduled successfully")

    def remove_existing_schedules(self):
        existing_schedules: QuerySet[Schedule] = Schedule.objects.filter(name=self.schedule_name)

        if not existing_schedules.exists():
            return

        logger.info(f"Removing {existing_schedules.count()} existing schedules")

        existing_schedules.delete()

    def schedule_task(self):
        function_args = ()
        if hasattr(self, "command_name"):
            function_args = (self.command_name,)
        if hasattr(self, "function_args"):
            function_args = function_args + self.function_args

        if not hasattr(self, "function_args") and not hasattr(self, "command_name"):
            raise ValueError("`function_args`, `command_name`, or both must be provided.")

        schedule(
            self.function_name,
            *function_args,
            name=self.schedule_name,
            **self.schedule_details,
        )
