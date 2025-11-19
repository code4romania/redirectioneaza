from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from donations.models.donors import Donor
from donations.models.ngos import Ngo
from editions.calendar import edition_deadline
from utils.common.filters import QueryFilter


class NgoQueryFilter(QueryFilter):
    ngo: Ngo | None = None

    def __init__(self, ngo):
        super().__init__()

        self.ngo = ngo


class FormYearQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_year"
        self.key = "year"
        self.type = "select"

        self.title = _("Years")

        self.queryset_key = "date_created__year"

    def options_default(self) -> list[dict[str, int | str]]:
        last_year = edition_deadline().year
        ngo_date_created = self.ngo.date_created
        year_range = range(ngo_date_created.year, last_year + 1)

        return [{"title": str(year), "value": str(year)} for year in year_range]


class CountyQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_county"
        self.key = "county"
        self.type = "combobox"

        self.title = _("County")

        self.queryset_key = "county"

    def options_with_objects(self, objects: QuerySet[Donor] | None = None) -> list[dict[str, int | str]]:
        all_counties = objects.values_list("county", flat=True).distinct()
        return [county for county in settings.COUNTIES_WITH_SECTORS_LIST if county in all_counties]

    def options_default(self) -> list[dict[str, int | str]]:
        return [{"title": county, "value": county} for county in settings.COUNTIES_WITH_SECTORS_LIST]


class LocalityQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_locality"
        self.key = "city"
        self.type = "combobox"

        self.title = _("Locality")

        self.queryset_key = "city"

    def options_with_objects(self, objects: QuerySet | None = None) -> list[dict[str, int | str]]:
        return sorted(set(objects.values_list("city", flat=True).distinct()))

    def options_default(self) -> list[dict[str, int | str]]:
        return []


class FormPeriodQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_period"
        self.key = "period"
        self.type = "select"

        self.title = _("Period")

        self.queryset_key = "two_years"
        self.transform_queryset = lambda fe_value: fe_value == "2"

    def options_default(self) -> list[dict[str, int | str]]:
        return [
            {"title": _("One year"), "value": "1"},
            {"title": _("Two years"), "value": "2"},
        ]


class FormStatusQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_status"
        self.key = "signed"
        self.type = "select"

        self.title = _("Status")

        self.queryset_key = "has_signed"
        self.transform_queryset = lambda fe_value: fe_value == "signed"

    def options_default(self) -> list[dict[str, int | str]]:
        return [
            {"title": _("Signed"), "value": "signed"},
            {"title": _("Not signed"), "value": "unsigned"},
        ]


class FormAnonymousQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_anonymous"
        self.key = "anonymous"
        self.type = "select"

        self.title = _("Is Anonymous")

        self.queryset_key = "is_anonymous"
        self.transform_queryset = lambda fe_value: fe_value == "da"

    def options_default(self) -> list[dict[str, int | str]]:
        return [
            {"title": _("Anonymous"), "value": "da"},
            {"title": _("Not anonymous"), "value": "nu"},
        ]


class CauseQueryFilter(NgoQueryFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = "filter_dropdown_cause"
        self.key = "cause"
        self.type = "combobox"

        self.title = _("Cause")

        self.queryset_key = "cause_id"

    def options_default(self) -> list[dict[str, int | str]]:
        if not self.ngo:
            return []

        if self.ngo.causes.count() <= 1:
            return []

        options = []
        for cause in self.ngo.causes.all():
            options.append({"title": cause.name, "value": cause.pk})

        return options


def get_redirections_filters(ngo: Ngo) -> list[QueryFilter]:
    return [
        FormYearQueryFilter(ngo=ngo),
        CountyQueryFilter(ngo=ngo),
        LocalityQueryFilter(ngo=ngo),
        FormPeriodQueryFilter(ngo=ngo),
        FormStatusQueryFilter(ngo=ngo),
        FormAnonymousQueryFilter(ngo=ngo),
        CauseQueryFilter(ngo=ngo),
    ]


def get_active_filters(filters: list[QueryFilter], request_params: dict) -> list[dict[str, QueryFilter | Any]]:
    active_filters = []

    for search_filter in filters:
        filter_key = search_filter.key
        if filter_value := request_params.get(filter_key, ""):
            active_filters.append(
                {
                    "filter": search_filter,
                    "value": filter_value,
                    "value_title": search_filter.title_for_option(filter_value),
                }
            )

    return active_filters


def get_active_filters_values(filters: list[QueryFilter], request_params: dict) -> dict[str, Any]:
    active_filters_values = {}
    active_filters = get_active_filters(filters, request_params)
    for active_filter in active_filters:
        filter_key = active_filter["filter"].key
        filter_value = active_filter["value"]
        active_filters_values[filter_key] = filter_value

    return active_filters_values


def get_queryset_filters(filters: list[QueryFilter], request_params: dict) -> dict[str, Any]:
    queryset_filters = {}

    for search_filter in filters:
        filter_key = search_filter.key
        if filter_value := request_params.get(filter_key, ""):
            queryset_filters[search_filter.queryset_key] = search_filter.transform_to_qs_value(filter_value)

    return queryset_filters
