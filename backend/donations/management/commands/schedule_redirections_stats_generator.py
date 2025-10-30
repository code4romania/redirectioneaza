import logging
from datetime import date
from typing import Set

from django.core.management import BaseCommand
from django_q.tasks import async_task

from donations.models import Donor
from donations.models.stat_configs import StatsChoices, create_stat
from stats.models import Stat

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Schedule a generator that looks over all of the dates that are supposed to have donation stats and generates them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force regeneration of stats even if they already exist for certain dates.",
            default=False,
        )

    def handle(self, *args, **kwargs):
        force: bool = kwargs.get("force", False)

        target_set: Set[date] = {
            dt.date() for dt in (Donor.available.all().values_list("date_created", flat=True).distinct())
        }

        if not force:
            existing_stats_dates: Set[date] = set(
                Stat.objects.filter(name=StatsChoices.REDIRECTIONS_PER_DAY).values_list("date", flat=True).distinct()
            )

            target_set: Set[date] = target_set - existing_stats_dates

        for single_date in target_set:
            async_task(
                create_stat,
                stat_choice=StatsChoices.REDIRECTIONS_PER_DAY,
                for_date=single_date,
            )
