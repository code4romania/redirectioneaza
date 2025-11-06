from datetime import date
from typing import List

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


def get_current_year_range() -> List[int]:
    """
    Returns a list of years from the start year to the current year.
    """
    current_year: int = timezone.now().year
    return list(range(settings.START_YEAR, current_year + 1))
