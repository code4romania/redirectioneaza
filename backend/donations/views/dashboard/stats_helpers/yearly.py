from datetime import datetime
from typing import Any, Dict

from django.utils.timezone import now

from donations.models import Donor, Ngo
from donations.views.dashboard.stats_helpers.utils import cache_set

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


def _update_stats_for_year(year: int, _cache_key: str = None, _timeout: int = None) -> Dict[str, Any]:
    """
    Updates the statistics for a given year and caches the result.

    Parameters:
        year (int): The year for which to compute statistics.
        _cache_key (str, optional): The cache key to use when storing the result.
        _timeout (int, optional): The cache timeout in seconds.

    Returns:
        Dict[str, Any]: A dictionary containing statistics for the specified year.
    """
    current_time: datetime = now()

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

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, statistic, timeout=_timeout)

    return statistic
