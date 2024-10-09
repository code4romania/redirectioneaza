import json
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import localtime, now
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlencode

from donations.models.main import Donor, Ngo
from redirectioneaza.common.cache import cache_decorator

ADMIN_DASHBOARD_CACHE_KEY = "ADMIN_DASHBOARD"


@cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=ADMIN_DASHBOARD_CACHE_KEY)
def callback(request, context):
    today = now()
    current_year = today.year
    years_range = range(current_year, settings.START_YEAR, -1)

    donations_this_year = Donor.objects.filter(date_created__year=current_year).count()
    donations_all_time = Donor.objects.count()
    ngos_total = Ngo.active.count()
    ngos_ngohub = Ngo.ngo_hub.count()

    messages.warning(
        request,
        render_to_string(
            "admin/announcements/work_in_progress.html",
            context={
                "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            },
        ),
    )

    start_of_this_year = datetime(year=current_year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=today.tzinfo)
    end_of_next_year = start_of_this_year.replace(year=current_year + 1)
    current_year_range: str = urlencode(
        {
            "date_created__gte": localtime(start_of_this_year),
            "date_created__lt": localtime(end_of_next_year),
        }
    )

    main_stats = [
        {
            "title": _("Donations this year"),
            "icon": "edit_document",
            "metric": donations_this_year,
            "footer": mark_safe(
                f'<a href="{reverse("admin:donations_donor_changelist")}?{current_year_range}">{_("View all")}</a>'
            ),
            "footer_class": "bg-gray-100 text-sm",
        },
        {
            "title": _("Donations all-time"),
            "icon": "edit_document",
            "metric": donations_all_time,
            "footer": mark_safe(f'<a href="{reverse("admin:donations_donor_changelist")}">{_("View all")}</a>'),
            "footer_class": "bg-gray-100 text-sm",
        },
        {
            "title": _("NGOs registered"),
            "icon": "foundation",
            "metric": ngos_total,
            "footer": mark_safe(
                f'<a href="{reverse("admin:donations_ngo_changelist")}?is_active=1">{_("View all")}</a>'
            ),
            "footer_class": "bg-gray-100 text-sm",
        },
        {
            "title": _("NGOs from NGO Hub"),
            "icon": "foundation",
            "metric": ngos_ngohub,
            "footer": mark_safe(
                f'<a href="{reverse("admin:donations_ngo_changelist")}?is_active=1&is_ngohub=1">{_("View all")}</a>'
            ),
            "footer_class": "bg-gray-100 text-sm",
        },
    ]

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
            "border_width": 3 if year == current_year else 2,
        }
        for year in years_range
    ]

    forms_per_month_chart = json.dumps(
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
                    "borderWidth": data["border_width"],
                }
                for data in dataset_parameters
            ],
        }
    )

    context.update(
        {
            "main_stats": main_stats,
            "forms_per_month_chart_title": _("Donations per month"),
            "forms_per_month_chart": forms_per_month_chart,
        }
    )

    return context
