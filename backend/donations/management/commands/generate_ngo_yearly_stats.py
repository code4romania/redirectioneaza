import logging
from datetime import date
from typing import Set

from django.core.management import BaseCommand
from django.utils.timezone import now
from django_q.tasks import async_task

from donations.models.stat_configs import StatsChoices, create_stat
from donations.views.dashboard.helpers import get_current_year_range
from stats.models import Stat

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run a task that generates redirection statistics for all ngos."

    choices = [
        StatsChoices.NGOS_REGISTERED_PER_YEAR,
        StatsChoices.NGOS_ACTIVE_PER_YEAR,
        StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR,
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force regeneration of stats even if they already exist for certain dates.",
            default=False,
        )
        parser.add_argument(
            "statistic",
            type=str,
            help="What type of statistic to generate",
            choices=self.choices,
        )

    def handle(self, *args, **kwargs):
        """
        Generate redirection statistics for ngos.
        `force` argument forces regeneration of stats even if they already exist.
        If the `force` argument is not provided, the command will only generate stats for dates
        that do not already have stats recorded and expired stats will be cleaned up first.
        """
        statistic: str = kwargs["statistic"]
        force: bool = kwargs.get("force", False)

        target_years: Set[int] = set(get_current_year_range())

        if not force:
            # Get existing stats dates that are not expired
            existing_stats_dates: Set[int] = set(
                Stat.objects.filter(name=statistic)
                .exclude(expires_at__lte=now())
                .values_list("date__year", flat=True)
                .distinct()
            )

            target_years: Set[int] = target_years - existing_stats_dates

        for target_year in target_years:
            async_task(
                create_stat,
                stat_choice=statistic,
                for_date=date(year=target_year, month=1, day=1),
            )
