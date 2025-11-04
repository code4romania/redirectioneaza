import calendar
from datetime import date
from decimal import Decimal

from django.utils.timezone import now

from donations.models.stat_configs import StatsChoices
from stats.api import get_stats_total_between_dates

STATS_FOR_MONTH_CACHE_PREFIX = "STATS_FOR_MONTH_"


# TODO: Implement caching properly
def donors_for_month(month: int, year: int = None) -> Decimal:
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
        Decimal: The number of donors for the specified month and year.
    """
    if year is None:
        year = now().year

    return _update_stats_for_month(month, year)


def _update_stats_for_month(month: int, year: int) -> Decimal:
    """
    Updates the number of donors for a specific month and year, and caches the result.

    Parameters:
        month (int): The month for which to compute donor statistics.
        year (int): The year for which to compute donor statistics.

    Returns:
        Decimal: The number of donors for the specified month and year.
    """
    donors_in_month: Decimal = get_stats_total_between_dates(
        key_name=StatsChoices.REDIRECTIONS_PER_DAY,
        from_date=date(year=year, month=month, day=1),
        to_date=date(year=year, month=month, day=calendar.monthrange(year, month)[1]),
    )

    return donors_in_month
