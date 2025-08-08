from datetime import datetime
from typing import Dict

from django.core.cache import cache
from django.utils.timezone import now
from django_q.tasks import async_task

from donations.models import Donor
from donations.views.dashboard.stats_helpers.utils import cache_set

STATS_FOR_MONTH_CACHE_PREFIX = "STATS_FOR_MONTH_"


def donors_for_month(month: int, year: int = None) -> Dict[str, int]:
    """
    Determines the number of donors for a specified month and year.

    This function retrieves the number of donors for a specific month and year
    from the cache if available and valid. If the cache is invalid or absent,
    it initiates an asynchronous task to update the stats and returns a default
    statistic. If the year parameter is not provided, it defaults to the
    current year.

    Parameters:
        month (int): The month for which donor statistics are requested.
        year (int, optional): The year for which donor statistics are required or current year.

    Returns:
        Dict[str, int]: A dictionary containing the number of donors for the specified month and year.
    """
    current_time = now()

    if year is None:
        year = current_time.year

    cache_key = f"{STATS_FOR_MONTH_CACHE_PREFIX}{year}_{month}"

    if cached_stats := cache.get(cache_key):
        if _is_cache_valid(current_time, month, year):
            return cached_stats

        cache.delete(cache_key)

    default_stat = {
        "metric": -2,
        "year": year,
        "month": month,
    }

    async_task(
        _update_stats_for_month,
        month,
        year,
        cache_key,
    )

    return cached_stats or default_stat


def _is_cache_valid(current_time: datetime, month: int, year: int) -> bool:
    if not current_time:
        return False

    if year < current_time.year:
        return True

    if month < current_time.month:
        return True

    return False


def _update_stats_for_month(month: int, year: int, cache_key: str) -> Dict[str, int]:
    """
    Updates the number of donors for a specific month and year, and caches the result.
    If the cache is valid, it returns the cached number of donors.
    """
    donors_count = Donor.objects.filter(date_created__year=year, date_created__month=month).count()

    stat = {
        "metric": donors_count,
        "year": year,
        "month": month,
    }

    cache_set(cache_key, stat)

    return stat
