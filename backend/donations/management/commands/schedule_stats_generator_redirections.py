import logging
from datetime import timedelta

from django.utils import timezone
from django_q.models import Schedule

from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a recurring task to generate donation statistics."

    command_name: str = "generate_redirections_stats"

    schedule_name: str = "GENERATE_STATS_REDIRECTIONS"
    schedule_details = {
        "schedule_type": Schedule.MINUTES,
        "minutes": 5,
        "repeats": -1,
        "next_run": timezone.now() + timedelta(minutes=0),
    }
