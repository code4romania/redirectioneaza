from datetime import datetime, tzinfo
from typing import Dict, List, Union

from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from donations.views.dashboard.stats_helpers.metrics import (
    all_redirections,
    all_registered_ngos,
    current_year_redirections,
    ngos_active_in_current_year,
    ngos_with_ngo_hub,
)
from donations.views.dashboard.stats_helpers.yearly import get_stats_for_year
from editions.calendar import edition_deadline, get_current_year_range
from redirectioneaza.common.cache import cache_decorator

from .helpers import (
    generate_donations_per_month_chart,
    get_encoded_current_year_range,
)
from .stats_helpers.chart import donors_for_month
from .stats_helpers.utils import format_stat_link, format_yearly_stats

ADMIN_DASHBOARD_HEADER_CACHE_KEY = "ADMIN_DASHBOARD_HEADER"
ADMIN_DASHBOARD_CHART_CACHE_KEY = "ADMIN_DASHBOARD_CHART"
ADMIN_DASHBOARD_YEARLY_CACHE_KEY = "ADMIN_DASHBOARD_YEARLY"


def callback(_, context) -> Dict:
    context.update(_get_admin_stats())
    return context


def _get_admin_stats() -> Dict:
    years_range_ascending = get_current_year_range()

    header_stats: List[List[Dict[str, Union[str, int]]]] = _get_header_stats()

    yearly_stats: List[Dict] = _get_yearly_stats(years_range_ascending)

    forms_per_month_chart: Dict[str, str] = _create_chart_statistics()

    return {
        "header_stats": header_stats,
        "yearly_stats": yearly_stats,
        "forms_per_month_chart": forms_per_month_chart,
    }


@cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key=ADMIN_DASHBOARD_HEADER_CACHE_KEY)
def _get_header_stats() -> List[List[Dict[str, Union[str, int | datetime]]]]:
    today: datetime = now()

    current_year: int = today.year
    tz_info: tzinfo = today.tzinfo

    current_year_range = get_encoded_current_year_range(current_year, tz_info)

    return [
        [
            {
                "title": _("Donations this year"),
                "icon": "edit_document",
                "metric": current_year_redirections(),
                "footer": format_stat_link(
                    url=f"{reverse('admin:donations_donor_changelist')}?{current_year_range}",
                    text=_("View all"),
                ),
            },
            {
                "title": _("Donations all-time"),
                "icon": "edit_document",
                "metric": all_redirections(),
                "footer": format_stat_link(
                    url=reverse("admin:donations_donor_changelist"),
                    text=_("View all"),
                ),
            },
            {
                "title": _("NGOs registered"),
                "icon": "foundation",
                "metric": all_registered_ngos(),
                "footer": format_stat_link(
                    url=f"{reverse('admin:donations_ngo_changelist')}?is_active=1",
                    text=_("View all"),
                ),
            },
            {
                "title": _("Functioning NGOs"),
                "icon": "foundation",
                "metric": ngos_active_in_current_year(),
                "footer": format_stat_link(
                    url=f"{reverse('admin:donations_ngo_changelist')}",
                    text=_("View all"),
                ),
            },
            {
                "title": _("NGOs from NGO Hub"),
                "icon": "foundation",
                "metric": ngos_with_ngo_hub(),
                "footer": format_stat_link(
                    url=f"{reverse('admin:donations_ngo_changelist')}?is_active=1&has_ngohub=1",
                    text=_("View all"),
                ),
            },
        ]
    ]


@cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key=ADMIN_DASHBOARD_CHART_CACHE_KEY)
def _create_chart_statistics() -> Dict[str, str]:
    default_border_width: int = 3
    year_range_ascending = get_current_year_range()

    donations_per_year: Dict[int, List[int]] = {}
    for year in year_range_ascending:
        donations_per_year[year] = [
            int(donors_for_month(month=month, year=year)) for month in range(1, edition_deadline().month + 1)
        ]

    return generate_donations_per_month_chart(default_border_width, donations_per_year)


@cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key=ADMIN_DASHBOARD_YEARLY_CACHE_KEY)
def _get_yearly_stats(years_range_ascending) -> List[Dict[str, Union[int, List[Dict]]]]:
    statistics = [get_stats_for_year(year) for year in years_range_ascending]

    for index, statistic in enumerate(statistics):
        if index == 0:
            continue

        statistics[index]["donations_difference"] = statistics[index]["donations"] - statistics[index - 1]["donations"]
        statistics[index]["ngos_registered_difference"] = (
            statistics[index]["ngos_registered"] - statistics[index - 1]["ngos_registered"]
        )
        statistics[index]["ngos_with_forms_difference"] = (
            statistics[index]["ngos_with_forms"] - statistics[index - 1]["ngos_with_forms"]
        )

    final_statistics = format_yearly_stats(statistics)

    return sorted(final_statistics, key=lambda x: x["year"], reverse=True)
