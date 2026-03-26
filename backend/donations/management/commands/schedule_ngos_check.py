import logging
from datetime import timedelta

from django.utils import timezone
from django_q.models import Schedule

from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a recurring task to check NGOs in ANAF Cult Registry"

    command_name: str = "check_ngos"

    schedule_details = {
        "schedule_type": Schedule.MINUTES,
        "minutes": 12,
        "repeats": -1,
        "next_run": timezone.now() + timedelta(minutes=0),
    }

    def handle(self, *args, **kwargs):
        self.schedule_name = "CHECK_NGOS"
        self.function_args = tuple()

        super().handle(*args, **kwargs)
