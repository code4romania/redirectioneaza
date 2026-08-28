from datetime import date

from django.conf import settings
from django.utils import timezone


def edition_deadline() -> date:
    """
    Returns the date limit for the current edition based on settings.
    """
    if settings.REDIRECTIONS_LIMIT_TO_CURRENT_YEAR:
        year: int = timezone.now().year
    else:
        year: int = settings.REDIRECTIONS_DEADLINE_YEAR

    month: int = settings.REDIRECTIONS_DEADLINE_MONTH
    day: int = settings.REDIRECTIONS_DEADLINE_DAY

    return date(year=year, month=month, day=day)


def get_current_year_range() -> list[int]:
    """
    Returns a list of years from the start year to the current year.
    """
    current_year: int = timezone.now().year
    return list(range(settings.START_YEAR, current_year + 1))


def january_first():
    """
    Returns a timezone aware datetime for January 1st of the current year
    """
    return timezone.localtime(timezone.now()).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
