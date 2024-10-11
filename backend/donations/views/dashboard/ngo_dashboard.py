from typing import Dict, List, Union

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from donations.models.main import Donor, Ngo
from redirectioneaza import settings
from redirectioneaza.common.cache import cache_decorator

from .helpers import generate_donations_per_month_chart

UserModel = get_user_model()

NGO_YEAR_RANGE_CACHE_KEY = "NGO_YEAR_RANGE"


def callback(request, context) -> Dict:
    user: UserModel = request.user
    if user.ngo is None:
        return context

    user_ngo = user.ngo

    header_stats = _get_header_stats(user_ngo)
    table_stats = _get_donations_per_county(user_ngo)
    forms_per_month_chart: Dict[str, str] = _create_chart_statistics(user_ngo)

    context.update(
        {
            "header_stats": header_stats,
            "table_stats": table_stats,
            "forms_per_month_chart": forms_per_month_chart,
        }
    )

    return context


def _create_chart_statistics(organization: Ngo) -> Dict[str, str]:
    default_border_width: int = 3

    donations_per_month_queryset = [
        Donor.objects.filter(date_created__month=month, ngo=organization)
        for month in range(1, settings.DONATIONS_LIMIT.month + 1)
    ]

    forms_per_month_chart = generate_donations_per_month_chart(default_border_width, donations_per_month_queryset)

    return forms_per_month_chart


def _get_donations_per_county(user_ngo):
    headers = [
        "#",
        _("County"),
        _("Number of donations"),
    ]

    counties = Donor.objects.filter(ngo=user_ngo).values_list("county", flat=True).distinct()

    rows = [
        [
            county,
            Donor.objects.filter(ngo=user_ngo, county=county).count(),
        ]
        for county in counties
    ]
    # sort by number of donations
    rows = sorted(rows, key=lambda x: x[1], reverse=True)

    # add the row index
    rows = [[index + 1] + row for index, row in enumerate(rows)]

    return {
        "title": _("Current year donations per county"),
        "data": {
            "headers": headers,
            "rows": rows,
        },
    }


def _get_header_stats(ngo: Ngo) -> List[List[Dict[str, Union[str, int]]]]:
    organization_year_range = _get_ngo_year_range(ngo)

    years_per_row = 4
    year_rows = [
        organization_year_range[i : i + years_per_row][::-1]
        for i in range(0, len(organization_year_range), years_per_row)
    ][::-1]

    header_stats = [
        [
            {
                "title": _("Donations in %d") % year,
                "icon": "edit_document",
                "metric": Donor.objects.filter(date_created__year=year).count(),
            }
            for year in year_row
        ]
        for year_row in year_rows
    ]

    return header_stats


@cache_decorator(timeout=settings.TIMEOUT_CACHE_LONG, cache_key_prefix=NGO_YEAR_RANGE_CACHE_KEY)
def _get_ngo_year_range(ngo: Ngo) -> List[int]:
    ngo_year_created = ngo.date_created.year

    return list(range(ngo.date_created.year, ngo_year_created + 1))
