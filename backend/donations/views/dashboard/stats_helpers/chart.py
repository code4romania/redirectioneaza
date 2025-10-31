from datetime import datetime
from typing import Any, Dict, Union

from django.utils.timezone import now

from donations.models import Donor
from donations.views.dashboard.stats_helpers.utils import cache_set

STATS_FOR_MONTH_CACHE_PREFIX = "STATS_FOR_MONTH_"


# TODO: Implement caching properly
def donors_for_month(month: int, year: int = None) -> Dict[str, Any]:
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
        Dict[str, Any]: A dictionary containing the number of donors for the specified month and year.
    """
    if year is None:
        year = now().year

    return _update_stats_for_month(month, year)


def _update_stats_for_month(
    month: int, year: int, _cache_key: str = None, _timeout: int = None
) -> Dict[str, Union[int, datetime]]:
    """
    Updates the number of donors for a specific month and year, and caches the result.

    Parameters:
        month (int): The month for which to compute donor statistics.
        year (int): The year for which to compute donor statistics.
        _cache_key (str, optional): The cache key to use when storing the result.
        _timeout (int, optional): The cache timeout in seconds.

    Returns:
        Dict[str, Any]: A dictionary containing the number of donors for the specified month and year.
    """
    donors_count: int = Donor.objects.filter(date_created__year=year, date_created__month=month).count()

    stat = {
        "metric": donors_count,
        "year": year,
        "month": month,
        "timestamp": now(),
    }

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, stat, timeout=_timeout)

    return stat
