from datetime import date, datetime
from typing import Any, Dict

from django.utils.timezone import now

from donations.models import Donor, Ngo
from donations.models.stat_configs import StatsChoices
from stats.api import get_stats_total_between_dates

STATS_FOR_YEAR_CACHE_PREFIX = "STATS_FOR_YEAR_"


# TODO: Implement caching properly
def get_stats_for_year(year: int) -> Dict[str, Any]:
    """
    Fetches and returns statistics for a given year.

    This function attempts to retrieve cached statistics for the specified year from the
    cache. If the cache is valid, the cached statistics are returned. Otherwise, the cache
    is cleared, and default placeholder statistics are returned. Additionally, an
    asynchronous task is triggered to update the statistics for the given year and store
    them in the cache.

    Parameters:
    year (int): The year for which to retrieve statistics.

    Returns:
    Dict[str, Any]: A dictionary containing statistics for the specified year.
    The dictionary includes:
        - "year" (int): The year of the statistics.
        - "donations" (int): The number of donations.
        - "ngos_registered" (int): The number of NGOs registered.
        - "ngos_with_forms" (int): The number of NGOs with forms.
        - "timestamp" (datetime): The timestamp indicating when the statistics were computed.
    """
    return _update_stats_for_year(year)


def _update_stats_for_year(year: int) -> Dict[str, Any]:
    """
    Updates the statistics for a given year and caches the result.

    Parameters:
        year (int): The year for which to compute statistics.

    Returns:
        Dict[str, Any]: A dictionary containing statistics for the specified year.
    """
    current_time: datetime = now()

    donations: int = int(
        get_stats_total_between_dates(
            key_name=StatsChoices.REDIRECTIONS_PER_DAY,
            from_date=date(year=year, month=1, day=1),
            to_date=date(year=year, month=12, day=31),
        )
    )
    ngos_registered: int = Ngo.objects.filter(date_created__year=year).count()
    ngos_with_forms: int = Donor.available.filter(date_created__year=year).values("ngo_id").distinct().count()

    statistic = {
        "year": year,
        "donations": donations,
        "ngos_registered": ngos_registered,
        "ngos_with_forms": ngos_with_forms,
        "timestamp": current_time,
    }

    return statistic
