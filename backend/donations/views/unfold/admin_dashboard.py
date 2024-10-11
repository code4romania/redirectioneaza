import json
from datetime import datetime
from typing import Dict

from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime, now
from django.utils.translation import gettext_lazy as _

from donations.models.main import Donor, Ngo
from redirectioneaza.common.cache import cache_decorator

ADMIN_DASHBOARD_CACHE_KEY = "ADMIN_DASHBOARD"


@cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=ADMIN_DASHBOARD_CACHE_KEY)
def admin_callback(request, context):
    today = now()
    years_range_ascending = range(settings.START_YEAR, today.year + 1)

    messages.warning(
        request,
        render_to_string(
            "admin/announcements/work_in_progress.html",
            context={
                "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            },
        ),
    )

    header_stats = _get_header_stats(today)

    yearly_stats = _get_yearly_stats(years_range_ascending)

    forms_per_month_chart = _create_chart_statistics(years_range_ascending)

    context.update(
        {
            "header_stats": header_stats,
            "yearly_stats": yearly_stats,
            "forms_per_month_chart": forms_per_month_chart,
        }
    )

    return context


def _get_header_stats(today):
    current_year = today.year

    start_of_this_year = datetime(year=current_year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=today.tzinfo)
    end_of_next_year = start_of_this_year.replace(year=current_year + 1)

    current_year_range: str = urlencode(
        {
            "date_created__gte": localtime(start_of_this_year),
            "date_created__lt": localtime(end_of_next_year),
        }
    )

    return [
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


def _create_chart_statistics(years_range_ascending):
    default_border_width: int = 3

    donations_per_month_queryset = [
        Donor.objects.filter(date_created__month=month) for month in range(1, settings.DONATIONS_LIMIT.month + 1)
    ]

    dataset_parameters = [
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

    forms_per_month_chart = {
        "title": _("Donations per month"),
        "data": json.dumps(
            {
                "labels": [str(month["label"]) for month in settings.MONTHS[: settings.DONATIONS_LIMIT.month]],
                "datasets": [
                    {
                        "label": str(data["year"]),
                        "data": [
                            donations.filter(date_created__year=data["year"]).count()
                            for donations in donations_per_month_queryset
                        ],
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


def _get_yearly_stats(years_range_ascending):
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


def _format_yearly_stats(statistics):
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
