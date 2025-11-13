from datetime import date
from decimal import Decimal

from django.conf import settings
from django.utils.timezone import now

from donations.models.stat_configs import StatsChoices
from editions.calendar import edition_deadline
from stats.api import get_single_total_stat, get_stats_total_between_dates


def _get_end_date() -> date:
    today: date = now().date()

    if today <= edition_deadline():
        year = today.year
        month = today.month
        day = today.day
    else:
        year = edition_deadline().year
        month = edition_deadline().month
        day = edition_deadline().day

    return date(year=year, month=month, day=day)


def current_year_redirections() -> int:
    """
    Returns the number of redirections (donations) for the current year.

    Returns:
        int: The number of redirections for the current year.
    """
    stats_key: str = str(StatsChoices.REDIRECTIONS_PER_DAY.value)

    end_date: date = _get_end_date()
    stats: Decimal = get_stats_total_between_dates(
        key_name=stats_key,
        from_date=date(year=end_date.year, month=1, day=1),
        to_date=end_date,
    )

    return int(stats)


def all_redirections() -> int:
    """
    Returns the total number of redirections (donations) across all years.

    Returns:
        dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    stats_key: str = str(StatsChoices.REDIRECTIONS_PER_DAY.value)

    end_date: date = _get_end_date()
    start_date = date(year=settings.START_YEAR, month=1, day=1)  # Assuming donations started from year 2000

    stats: Decimal = get_stats_total_between_dates(
        key_name=stats_key,
        from_date=start_date,
        to_date=end_date,
    )

    return int(stats)


def all_registered_ngos() -> int:
    """
    Returns the total number of registered and valid NGOs.

    Returns:
        int: The number of registered NGOs.
    """
    stats_key = str(StatsChoices.NGOS_REGISTERED.value)

    stats: Decimal = get_single_total_stat(key_name=stats_key)
    return int(stats)


def ngos_active_in_current_year() -> int:
    """
    Returns the number of NGOs that are active in the current year.

    Returns:
        int: The number of active NGOs.
    """
    stats_key = str(StatsChoices.NGOS_ACTIVE.value)

    stats: Decimal = get_single_total_stat(key_name=stats_key)
    return int(stats)


def ngos_with_ngo_hub() -> int:
    """
    Returns the number of NGOs that are part of the NGO Hub.

    Returns:
        int: The number of NGOs with NGO Hub.
    """
    stats_key = str(StatsChoices.NGOS_WITH_NGOHUB.value)

    stats: Decimal = get_single_total_stat(key_name=stats_key)
    return int(stats)
