from datetime import date
from decimal import Decimal

from django.db.models import Sum

from stats.models import Stat


def get_single_total_stat(*, key_name: str) -> Decimal:
    """
    Retrieves the total value of a single statistic key.

    Parameters:
        key_name (str): The name of the statistic key to retrieve.

    Returns:
        Decimal: The total value of the statistic key.
    """
    try:
        stat_result: Decimal = Stat.objects.get(name=key_name).value
    except Stat.DoesNotExist:
        return Decimal(0)

    return stat_result


def get_stats_total_between_dates(
    *,
    key_name: str,
    from_date: date,
    to_date: date,
) -> Decimal:
    """
    Retrieves multiple statistic key values in bulk.

    Parameters:
        key_name (list[str]): A list of statistic key names to retrieve.
        from_date (date): The start date for filtering the statistics.
        to_date (date): The end date for filtering the statistics.

    Returns:
        Decimal: The total value of the statistic keys within the specified date range.
    """
    returnable_stats = Stat.objects.filter(
        name=key_name,
        date__gte=from_date,
        date__lte=to_date,
    ).aggregate(total_value=Sum("value"))

    return returnable_stats["total_value"] or Decimal(0)
