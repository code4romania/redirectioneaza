import logging
from datetime import timedelta

from django.utils import timezone
from django_q.models import Schedule

from q_heartbeat.management.commands.qheartbeat import SCHEDULE_NAME
from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a heartbeat task to run every 10 minutes"

    command_name: str = "qheartbeat"

    schedule_name: str = SCHEDULE_NAME
    schedule_details = {
        "schedule_type": Schedule.MINUTES,
        "minutes": 10,
        "repeats": -1,
        "next_run": timezone.now() + timedelta(minutes=0),
    }
