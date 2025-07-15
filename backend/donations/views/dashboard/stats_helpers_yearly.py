from datetime import datetime
from typing import Dict

from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now
from django_q.tasks import async_task

from donations.models import Donor, Ngo


STATS_FOR_YEAR_CACHE_PREFIX = "STATS_FOR_YEAR_"


def get_stats_for_year(year: int) -> Dict[str, int | datetime]:
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
    Dict[str, int | datetime]: A dictionary containing statistics for the specified year.
    The dictionary includes:
        - "year" (int): The year of the statistics.
        - "donations" (int): Placeholder value (-2) for the number of donations.
        - "ngos_registered" (int): Placeholder value (-2) for the number of NGOs registered.
        - "ngos_with_forms" (int): Placeholder value (-2) for the number of NGOs with forms.
        - "timestamp" (datetime): The timestamp indicating the current retrieval time.
    """

    cache_key = f"{STATS_FOR_YEAR_CACHE_PREFIX}{year}"

    current_time: datetime = now()

    if cached_stats := cache.get(cache_key):
        cache_timestamp: datetime = cached_stats.get("timestamp", None)
        if _is_cache_valid(cache_timestamp, current_time):
            return cached_stats

        cache.delete(cache_key)

    default_stats = {
        "year": year,
        "donations": -2,
        "ngos_registered": -2,
        "ngos_with_forms": -2,
        "timestamp": current_time,
    }

    async_task(_update_stats_for_year, year, cache_key, current_time)

    return cached_stats or default_stats


def _is_cache_valid(cache_timestamp: datetime, current_time: datetime) -> bool:
    if not cache_timestamp:
        return False

    # If the timestamp is from a previous year, it's valid
    if cache_timestamp.year < current_time.year:
        return True

    # If the timestamp is from the current year,
    # it needs to be refreshed if the current time is before the end of the donation period
    if cache_timestamp > settings.DONATIONS_LIMIT:
        return True

    return False


def _update_stats_for_year(year: int, cache_key: str, current_time: datetime) -> Dict[str, int | datetime]:
    """
    Updates the statistics for a given year and caches the result.
    If the cache is valid, it returns the cached statistics.
    """
    donations: int = Donor.available.filter(date_created__year=year).count()
    ngos_registered: int = Ngo.objects.filter(date_created__year=year).count()
    ngos_with_forms: int = Donor.available.filter(date_created__year=year).values("ngo_id").distinct().count()

    statistic = {
        "year": year,
        "donations": donations,
        "ngos_registered": ngos_registered,
        "ngos_with_forms": ngos_with_forms,
        "timestamp": current_time,
    }

    cache.set(cache_key, statistic, timeout=settings.TIMEOUT_CACHE_NORMAL)

    return statistic
