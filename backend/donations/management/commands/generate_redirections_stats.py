import logging
from datetime import date

from django.core.management import BaseCommand
from django.utils.timezone import now
from django_q.tasks import async_task

from donations.models import Donor
from donations.models.stat_configs import StatsChoices, create_stat
from stats.models import Stat

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run a task that generates redirection statistics for all donors."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force regeneration of stats even if they already exist for certain dates.",
            default=False,
        )

    def handle(self, *args, **kwargs):
        """
        Generate redirection statistics for donors.
        `force` argument forces regeneration of stats even if they already exist.
        If the `force` argument is not provided, the command will only generate stats for dates
        that do not already have stats recorded and expired stats will be cleaned up first.
        """
        force: bool = kwargs.get("force", False)

        target_set: set[date] = {
            dt.date() for dt in (Donor.available.all().values_list("date_created", flat=True).distinct())
        }

        if not force:
            # Get existing stats dates that are not expired
            existing_stats_dates: set[date] = set(
                Stat.objects.filter(name=StatsChoices.REDIRECTIONS_PER_DAY)
                .exclude(expires_at__lte=now())
                .values_list("date", flat=True)
                .distinct()
            )

            target_set: set[date] = target_set - existing_stats_dates

        for single_date in target_set:
            async_task(
                create_stat,
                stat_choice=StatsChoices.REDIRECTIONS_PER_DAY,
                for_date=single_date,
            )
