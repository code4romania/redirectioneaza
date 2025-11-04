import logging
from datetime import timedelta
from typing import Dict, Tuple, Union

from django.utils import timezone
from django_q.models import Schedule

from donations.models.stat_configs import StatsChoices
from utils.common.commands import SchedulerCommand

logger = logging.getLogger(__name__)


class Command(SchedulerCommand):
    help = "Schedule a recurring task to generate ngos statistics."

    command_name: str = "generate_ngo_yearly_stats"

    schedule_prefix: str = "GENERATE_STATS_NGOS"
    schedule_details = {
        "schedule_type": Schedule.MINUTES,
        "minutes": 15,
        "repeats": -1,
        "next_run": timezone.now() + timedelta(minutes=0),
    }

    choices = [
        StatsChoices.NGOS_REGISTERED_PER_YEAR,
        StatsChoices.NGOS_REGISTERED,
        StatsChoices.NGOS_ACTIVE_PER_YEAR,
        StatsChoices.NGOS_ACTIVE,
        StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR,
        StatsChoices.NGOS_WITH_NGOHUB,
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "statistic",
            type=str,
            help="What type of statistic to generate",
            choices=self.choices,
        )

    def handle(self, *args, **kwargs):
        statistic: str = kwargs["statistic"]

        stat_mapping: Dict[str, Dict[str, Union[Tuple, str]]] = {
            StatsChoices.NGOS_REGISTERED_PER_YEAR: {
                "name": f"{self.schedule_prefix}_REGISTERED_PER_YEAR",
                "args": (StatsChoices.NGOS_REGISTERED_PER_YEAR.value,),
            },
            StatsChoices.NGOS_REGISTERED: {
                "name": f"{self.schedule_prefix}_REGISTERED_PER_YEAR",
                "args": (StatsChoices.NGOS_REGISTERED_PER_YEAR.value,),
            },
            StatsChoices.NGOS_ACTIVE_PER_YEAR: {
                "name": f"{self.schedule_prefix}_ACTIVE_PER_YEAR",
                "args": (StatsChoices.NGOS_ACTIVE_PER_YEAR.value,),
            },
            StatsChoices.NGOS_ACTIVE: {
                "name": f"{self.schedule_prefix}_ACTIVE_PER_YEAR",
                "args": (StatsChoices.NGOS_ACTIVE_PER_YEAR.value,),
            },
            StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR: {
                "name": f"{self.schedule_prefix}_WITH_NGOHUB_PER_YEAR",
                "args": (StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR.value,),
            },
            StatsChoices.NGOS_WITH_NGOHUB: {
                "name": f"{self.schedule_prefix}_WITH_NGOHUB_PER_YEAR",
                "args": (StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR.value,),
            },
        }

        if statistic not in stat_mapping:
            logger.error(f"Invalid statistic type provided: {statistic}")
            return

        self.schedule_name = stat_mapping[statistic]["name"]
        self.function_args = stat_mapping[statistic]["args"]

        super().handle(*args, **kwargs)
