import json
from datetime import datetime, tzinfo
from typing import Dict, List, Union
from urllib.parse import urlencode

from django.conf import settings
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from editions.calendar import edition_deadline, get_current_year_range
from redirectioneaza.common.cache import cache_decorator

ENCODED_CURRENT_YEAR_RANGE_CACHE_KEY = "ENCODED_CURRENT_YEAR_RANGE"
DATASET_PARAMETERS_CACHE_KEY = "DATASET_PARAMETERS"


@cache_decorator(timeout=settings.TIMEOUT_CACHE_LONG, cache_key_prefix=ENCODED_CURRENT_YEAR_RANGE_CACHE_KEY)
def get_encoded_current_year_range(current_year: int, tz_info: tzinfo) -> str:
    start_of_year: datetime = datetime(year=current_year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=tz_info)
    end_of_next_year: datetime = start_of_year.replace(year=current_year + 1)

    year_range: str = urlencode(
        {
            "date_created__gte": localtime(start_of_year),
            "date_created__lt": localtime(end_of_next_year),
        }
    )

    return year_range


@cache_decorator(timeout=settings.TIMEOUT_CACHE_LONG, cache_key_prefix=DATASET_PARAMETERS_CACHE_KEY)
def _get_chart_dataset_parameters() -> List[Dict[str, Union[int, str]]]:
    years_range_ascending = get_current_year_range()

    return [
        {
            "year": year,
            "border_color": (
                "rgba("
                f"{settings.CHART_COLORS[year % len(settings.CHART_COLORS)]['r']}, "
                f"{settings.CHART_COLORS[year % len(settings.CHART_COLORS)]['g']}, "
                f"{settings.CHART_COLORS[year % len(settings.CHART_COLORS)]['b']}, "
                "1)"
            ),
            "background_color": (
                "rgba("
                f"{settings.CHART_COLORS[year % len(settings.CHART_COLORS)]['r']}, "
                f"{settings.CHART_COLORS[year % len(settings.CHART_COLORS)]['g']}, "
                f"{settings.CHART_COLORS[year % len(settings.CHART_COLORS)]['b']}, "
                "0.2)"
            ),
        }
        for year in years_range_ascending
    ]


def generate_donations_per_month_chart(
    default_border_width: int, donations_per_month: Dict[int, List[int]]
) -> Dict[str, str]:
    dataset_parameters = _get_chart_dataset_parameters()
    forms_per_month_chart = {
        "title": _("Donations per month"),
        "data": json.dumps(
            {
                "labels": [str(month["label"]) for month in settings.MONTHS[: edition_deadline().month]],
                "datasets": [
                    {
                        "label": str(data["year"]),
                        "data": donations_per_month[data["year"]],
                        "borderColor": data["border_color"],
                        "backgroundColor": data["background_color"],
                        "borderWidth": data.get("border_width", default_border_width),
                    }
                    for data in dataset_parameters
                ],
            }
        ),
    }
    return forms_per_month_chart
