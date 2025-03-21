from typing import Dict, List, Optional, Union

from django.conf import settings
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.filters import QueryFilter


class CountyQueryFilter(QueryFilter):
    def __init__(self):
        self.id = "filter_dropdown_county"
        self.key = "c"
        self.type = "combobox"

        self.title = _("County")

        self.queryset_key = "county"

    def options_with_objects(self, objects: Optional[QuerySet] = None) -> List[Dict[str, Union[int, str]]]:
        all_counties = objects.values_list("county", flat=True).distinct()
        return [county for county in settings.COUNTIES_WITH_SECTORS_LIST if county in all_counties]

    def options_default(self) -> List[Dict[str, Union[int, str]]]:
        return settings.COUNTIES_WITH_SECTORS_LIST


class LocalityQueryFilter(QueryFilter):
    def __init__(self):
        self.id = "filter_dropdown_locality"
        self.key = "l"
        self.type = "combobox"

        self.title = _("Locality")

        self.queryset_key = "city"

    def options_with_objects(self, objects: Optional[QuerySet] = None) -> List[Dict[str, Union[int, str]]]:
        return sorted(set(objects.values_list("city", flat=True).distinct()))

    def options_default(self) -> List[Dict[str, Union[int, str]]]:
        return []


class FormPeriodQueryFilter(QueryFilter):
    def __init__(self):
        self.id = "filter_dropdown_period"
        self.key = "p"
        self.type = "select"

        self.title = _("Period")

        self.queryset_key = "two_years"
        self.queryset_transformation = lambda fe_value: fe_value == "2"

    def options_default(self) -> List[Dict[str, Union[int, str]]]:
        return [
            {"title": _("One year"), "value": "1"},
            {"title": _("Two years"), "value": "2"},
        ]


class FormStatusQueryFilter(QueryFilter):
    def __init__(self):
        self.id = "filter_dropdown_status"
        self.key = "s"
        self.type = "select"

        self.title = _("Status")

        self.queryset_key = "has_signed"
        self.queryset_transformation = lambda fe_value: fe_value == "signed"

    def options_default(self) -> List[Dict[str, Union[int, str]]]:
        return [
            {"title": _("Signed"), "value": "signed"},
            {"title": _("Not signed"), "value": "unsigned"},
        ]
