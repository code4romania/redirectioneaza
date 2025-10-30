import logging

from django_q.models import Schedule

from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a session cleanup task to run every day at 5:30 AM."

    command_name: str = "clearsessions"

    schedule_name = "CLEANUP_SESSIONS"
    schedule_details = {
        "schedule_type": Schedule.DAILY,
        "repeats": -1,
    }
