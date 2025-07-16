from datetime import datetime
from typing import Dict, List, Union

from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from donations.views.dashboard.stats_helpers.chart import donors_for_month
from donations.views.dashboard.stats_helpers.metrics import (
    all_active_ngos,
    all_redirections,
    current_year_redirections,
    ngos_active_in_current_year,
    ngos_with_ngo_hub,
)
from donations.views.dashboard.stats_helpers.yearly import get_stats_for_year

from .helpers import (
    generate_donations_per_month_chart,
    get_current_year_range,
    get_encoded_current_year_range,
)

ADMIN_DASHBOARD_CACHE_KEY = "ADMIN_DASHBOARD"
ADMIN_DASHBOARD_STATS_CACHE_KEY = "ADMIN_DASHBOARD_STATS"


def callback(request, context) -> Dict:
    context.update(_get_admin_stats())

    return context


def _get_admin_stats() -> Dict:
    today = now()
    years_range_ascending = get_current_year_range()

    header_stats: List[List[Dict[str, Union[str, int]]]] = _get_header_stats(today)

    yearly_stats: List[Dict] = _get_yearly_stats(years_range_ascending)

    forms_per_month_chart: Dict[str, str] = _create_chart_statistics()

    return {
        "header_stats": header_stats,
        "yearly_stats": yearly_stats,
        "forms_per_month_chart": forms_per_month_chart,
    }


def _get_header_stats(today) -> List[List[Dict[str, Union[str, int | datetime]]]]:
    current_year = today.year

    current_year_range = get_encoded_current_year_range(current_year, today.tzinfo)

    return [
        [
            {
                "title": _("Donations this year"),
                "icon": "edit_document",
                "metric": current_year_redirections["metric"],
                "footer": _create_stat_link(
                    url=f'{reverse("admin:donations_donor_changelist")}?{current_year_range}', text=_("View all")
                ),
                "timestamp": current_year_redirections["timestamp"],
            },
            {
                "title": _("Donations all-time"),
                "icon": "edit_document",
                "metric": all_redirections["metric"],
                "footer": _create_stat_link(url=reverse("admin:donations_donor_changelist"), text=_("View all")),
                "timestamp": all_redirections["timestamp"],
            },
            {
                "title": _("NGOs registered"),
                "icon": "foundation",
                "metric": all_active_ngos["metric"],
                "footer": _create_stat_link(
                    url=f'{reverse("admin:donations_ngo_changelist")}?is_active=1', text=_("View all")
                ),
                "timestamp": all_active_ngos["timestamp"],
            },
            {
                "title": _("Functioning NGOs"),
                "icon": "foundation",
                "metric": ngos_active_in_current_year["metric"],
                "footer": _create_stat_link(url=f'{reverse("admin:donations_ngo_changelist")}', text=_("View all")),
                "timestamp": ngos_active_in_current_year["timestamp"],
            },
            {
                "title": _("NGOs from NGO Hub"),
                "icon": "foundation",
                "metric": ngos_with_ngo_hub["metric"],
                "footer": _create_stat_link(
                    url=f'{reverse("admin:donations_ngo_changelist")}?is_active=1&has_ngohub=1', text=_("View all")
                ),
                "timestamp": ngos_with_ngo_hub["timestamp"],
            },
        ]
    ]


def _create_chart_statistics() -> Dict[str, str]:
    default_border_width: int = 3
    current_year = now().year

    donations_per_month_queryset = [
        donors_for_month(month, current_year)["metric"] for month in range(1, settings.DONATIONS_LIMIT.month + 1)
    ]

    forms_per_month_chart = generate_donations_per_month_chart(default_border_width, donations_per_month_queryset)

    return forms_per_month_chart


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

    final_statistics = _format_yearly_stats(statistics)

    return sorted(final_statistics, key=lambda x: x["year"], reverse=True)


def _format_yearly_stats(statistics) -> List[Dict[str, Union[int, List[Dict]]]]:
    return [
        {
            "year": statistic["year"],
            "stats": [
                {
                    "title": _("Donations"),
                    "icon": "edit_document",
                    "metric": statistic["donations"],
                    "label": statistic.get("donations_difference"),
                    "footer": _create_stat_link(
                        url=f'{reverse("admin:donations_donor_changelist")}?date_created__year={statistic["year"]}',
                        text=_("View all"),
                    ),
                    "timestamp": statistic["timestamp"],
                },
                {
                    "title": _("NGOs registered"),
                    "icon": "foundation",
                    "metric": statistic["ngos_registered"],
                    "label": statistic.get("ngos_registered_difference"),
                    "footer": _create_stat_link(
                        url=f'{reverse("admin:donations_ngo_changelist")}?date_created__year={statistic["year"]}',
                        text=_("View all"),
                    ),
                    "timestamp": statistic["timestamp"],
                },
                {
                    "title": _("NGOs with forms"),
                    "icon": "foundation",
                    "metric": statistic["ngos_with_forms"],
                    "label": statistic.get("ngos_with_forms_difference"),
                    "footer": _create_stat_link(
                        url=f'{reverse("admin:donations_ngo_changelist")}?has_forms=1&date_created__year={statistic["year"]}',
                        text=_("View all"),
                    ),
                    "timestamp": statistic["timestamp"],
                },
            ],
        }
        for statistic in statistics
    ]


def _create_stat_link(url: str, text: str) -> str:
    return mark_safe(f'<a href="{url}" class="text-orange-700 font-semibold">{text}</a>')
