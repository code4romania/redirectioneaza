import logging
from datetime import timedelta
from typing import Dict

from django.utils import timezone
from django_q.models import Schedule

from donations.models.stat_configs import StatsChoices
from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a recurring task to generate ngos statistics."

    command_name: str = "generate_stats"

    schedule_prefix: str = "GENERATE_STATS_NGOS"
    schedule_details = {
        "schedule_type": Schedule.MINUTES,
        "minutes": 15,
        "repeats": -1,
        "next_run": timezone.now() + timedelta(minutes=0),
    }

    choices = [StatsChoices.NGOS_REGISTERED, StatsChoices.NGOS_ACTIVE, StatsChoices.NGOS_WITH_NGOHUB]

    def add_arguments(self, parser):
        parser.add_argument(
            "statistic",
            type=str,
            help="What type of statistic to generate",
            choices=self.choices,
        )

    def handle(self, *args, **kwargs):
        statistic: str = kwargs["statistic"]

        stat_mapping: Dict[str, str] = {
            StatsChoices.NGOS_REGISTERED: f"{self.schedule_prefix}_REGISTERED",
            StatsChoices.NGOS_ACTIVE: f"{self.schedule_prefix}_ACTIVE",
            StatsChoices.NGOS_WITH_NGOHUB: f"{self.schedule_prefix}_WITH_NGOHUB",
        }

        if statistic not in stat_mapping:
            logger.error(f"Invalid statistic type provided: {statistic}")
            return

        self.schedule_name = stat_mapping[statistic]
        self.function_args = (statistic,)

        super().handle(*args, **kwargs)
