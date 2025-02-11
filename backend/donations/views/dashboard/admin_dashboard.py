from typing import Dict, List, Union

from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Ngo
from redirectioneaza.common.cache import cache_decorator

from ...models.donors import Donor
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


@cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key=ADMIN_DASHBOARD_STATS_CACHE_KEY)
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


def _get_header_stats(today) -> List[List[Dict[str, Union[str, int]]]]:
    current_year = today.year

    current_year_range = get_encoded_current_year_range(current_year, today.tzinfo)

    return [
        [
            {
                "title": _("Donations this year"),
                "icon": "edit_document",
                "metric": Donor.objects.filter(date_created__year=current_year).count(),
                "footer": _create_stat_link(
                    url=f'{reverse("admin:donations_donor_changelist")}?{current_year_range}', text=_("View all")
                ),
            },
            {
                "title": _("Donations all-time"),
                "icon": "edit_document",
                "metric": Donor.objects.count(),
                "footer": _create_stat_link(url=reverse("admin:donations_donor_changelist"), text=_("View all")),
            },
            {
                "title": _("NGOs registered"),
                "icon": "foundation",
                "metric": Ngo.active.count(),
                "footer": _create_stat_link(
                    url=f'{reverse("admin:donations_ngo_changelist")}?is_active=1', text=_("View all")
                ),
            },
            {
                "title": _("NGOs from NGO Hub"),
                "icon": "foundation",
                "metric": Ngo.ngo_hub.count(),
                "footer": _create_stat_link(
                    url=f'{reverse("admin:donations_ngo_changelist")}?is_active=1&is_ngohub=1', text=_("View all")
                ),
            },
        ]
    ]


def _create_chart_statistics() -> Dict[str, str]:
    default_border_width: int = 3

    donations_per_month_queryset = [
        Donor.objects.filter(date_created__month=month) for month in range(1, settings.DONATIONS_LIMIT.month + 1)
    ]

    forms_per_month_chart = generate_donations_per_month_chart(default_border_width, donations_per_month_queryset)

    return forms_per_month_chart


def _get_yearly_stats(years_range_ascending) -> List[Dict[str, Union[int, List[Dict]]]]:
    statistics = [_get_stats_for_year(year) for year in years_range_ascending]

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


@cache_decorator(timeout=settings.TIMEOUT_CACHE_NORMAL, cache_key_prefix=ADMIN_DASHBOARD_CACHE_KEY)
def _get_stats_for_year(year: int) -> Dict[str, int]:
    donations: int = Donor.objects.filter(date_created__year=year).count()
    ngos_registered: int = Ngo.objects.filter(date_created__year=year).count()
    ngos_with_forms: int = Donor.objects.filter(date_created__year=year).values("ngo_id").distinct().count()

    statistic = {
        "year": year,
        "donations": donations,
        "ngos_registered": ngos_registered,
        "ngos_with_forms": ngos_with_forms,
    }

    return statistic


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
                },
            ],
        }
        for statistic in statistics
    ]


def _create_stat_link(url: str, text: str) -> str:
    return mark_safe(f'<a href="{url}" class="text-orange-700 font-semibold">{text}</a>')
