import logging
from datetime import timedelta

from django.utils import timezone
from django_q.models import Schedule

from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a session cleanup task to run once a day"

    command_name: str = "clearsessions"

    schedule_name = "CLEANUP_SESSIONS"
    schedule_details = {
        "schedule_type": Schedule.DAILY,
        "repeats": -1,
        "next_run": timezone.now() + timedelta(minutes=40),
    }
