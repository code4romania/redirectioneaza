from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from django.utils.timezone import now

from donations.models.stat_configs import StatsChoices
from stats.api import get_stat_for_year, get_stats_total_between_dates

STATS_FOR_YEAR_CACHE_PREFIX = "STATS_FOR_YEAR_"


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

    donations: Decimal = get_stats_total_between_dates(
        key_name=StatsChoices.REDIRECTIONS_PER_DAY,
        from_date=date(year=year, month=1, day=1),
        to_date=date(year=year, month=12, day=31),
    )
    ngos_registered: Decimal = get_stat_for_year(
        key_name=StatsChoices.NGOS_REGISTERED_PER_YEAR,
        year=year,
    )
    ngos_with_forms: Decimal = get_stat_for_year(
        key_name=StatsChoices.NGOS_ACTIVE_PER_YEAR,
        year=year,
    )

    statistic = {
        "year": year,
        "donations": int(donations),
        "ngos_registered": int(ngos_registered),
        "ngos_with_forms": int(ngos_with_forms),
        "timestamp": current_time,
    }

    return statistic
