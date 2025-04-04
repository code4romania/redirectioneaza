from typing import Any, List, Optional

from django.conf import settings
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db.models import Q, QuerySet, Value
from django.db.models.functions import Greatest
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from donations.models.donors import Donor
from donations.models.ngos import Cause, Ngo
from redirectioneaza.common.cache import cache_decorator


class ConfigureSearch:
    @staticmethod
    def query(query: str, language_code: str) -> SearchQuery:
        if language_code == "ro":
            return SearchQuery(query, config="romanian_unaccent")

        return SearchQuery(query)

    @staticmethod
    def vector(search_fields: List[str], language_code: str) -> SearchVector:
        if language_code == "ro":
            return SearchVector(*search_fields, weight="A", config="romanian_unaccent")

        return SearchVector(*search_fields, weight="A")


class CommonSearchMixin(ListView):
    def get_search_results(self, queryset: QuerySet, query: str, language_code: str) -> QuerySet:
        raise NotImplementedError("You must add your own logic for searching")

    def _search_query(self) -> str:
        search_string = self.request.GET.get("q", "").strip()[:100]

        if len(search_string) < 3:
            return ""

        return search_string

    def _search_placeholder(self) -> str:
        search_string = self.request.GET.get("q", "").strip()

        if 0 < len(search_string) < 3:
            return _("The search query must be at least 3 characters long")

        return ""

    def search(self, queryset: Optional[QuerySet[Any]] = None) -> QuerySet:
        query = self._search_query()

        if not queryset:
            if not self.queryset:
                return queryset.none()
            queryset = self.queryset

        if not query or len(query) < settings.SEARCH_QUERY_MIN_LENGTH:
            return queryset.all()

        language_code: str = settings.LANGUAGE_CODE
        if hasattr(self.request, "LANGUAGE_CODE") and self.request.LANGUAGE_CODE:
            language_code = self.request.LANGUAGE_CODE
        language_code = language_code.lower()

        return self.get_search_results(queryset, query, language_code)


class NgoRegNumberSearchMixin(CommonSearchMixin):
    @classmethod
    def get_search_results(cls, queryset: QuerySet, query: str, language_code: str) -> QuerySet:
        search_fields = ["registration_number"]
        search_vector: SearchVector = ConfigureSearch.vector(search_fields, language_code)
        search_query: SearchQuery = ConfigureSearch.query(query, language_code)

        ngos: QuerySet[Ngo] = queryset.annotate(rank=SearchRank(search_vector, search_query)).filter(Q(rank__gte=0.3))

        return ngos


class CauseSearchMixin(CommonSearchMixin):
    @classmethod
    def get_search_results(cls, queryset: QuerySet, query: str, language_code: str) -> QuerySet[Cause]:
        search_fields = ["name"]
        search_vector: SearchVector = ConfigureSearch.vector(search_fields, language_code)
        search_query: SearchQuery = ConfigureSearch.query(query, language_code)

        causes: QuerySet[Cause] = (
            queryset.annotate(
                rank=SearchRank(search_vector, search_query),
                similarity=TrigramSimilarity("name", query),
            )
            .filter(Q(rank__gte=0.3) | Q(similarity__gt=0.1))
            .order_by("-rank", "-similarity", "name")
            .distinct()
        )

        return causes


class NgoCauseMixedSearchMixin(CommonSearchMixin):
    @classmethod
    @cache_decorator(timeout=settings.TIMEOUT_CACHE_NORMAL, cache_key_prefix="NGO_CAUSE_SEARCH")
    def get_search_results(cls, queryset: QuerySet, query: str, language_code: str) -> QuerySet[Cause]:
        """
        This method combines the results of NGO and Cause searches.
        If the search query is a 'CUI/CIF' (Romanian company registration number),
        it will return the main cause of the NGO with that registration number.
        Otherwise, it will return the causes that match the search query.
        It will likely never return results in both ngos_causes and searched_causes for the same query.
        """
        ngos = NgoRegNumberSearchMixin.get_search_results(Ngo.active, query, language_code)
        ngos_causes: QuerySet[Cause] = (
            Cause.public_active.annotate(rank=Value(1), similarity=Value(1))
            .filter(ngo__in=ngos, is_main=True)
            .distinct()
        )

        searched_causes: QuerySet[Cause] = CauseSearchMixin.get_search_results(queryset, query, language_code)

        return ngos_causes | searched_causes


class DonorSearchMixin(CommonSearchMixin):
    @classmethod
    def get_search_results(cls, queryset: QuerySet[Donor], query: str, language_code: str) -> QuerySet:
        search_fields = ["f_name", "l_name"]
        name_search_vector: SearchVector = ConfigureSearch.vector(search_fields, language_code)
        name_search_query: SearchQuery = ConfigureSearch.query(query, language_code)

        contact_search_fields = ["email", "phone"]
        contact_search_vector: SearchVector = ConfigureSearch.vector(contact_search_fields, language_code)
        contact_search_query: SearchQuery = ConfigureSearch.query(query, language_code)

        donors: QuerySet = queryset.annotate(
            rank=SearchRank(name_search_vector, name_search_query),
            similarity=Greatest(TrigramSimilarity("f_name", query), TrigramSimilarity("l_name", query)),
        ).filter(Q(rank__gte=0.3) | Q(similarity__gt=0.3))

        contact_donors = (
            queryset.annotate(
                rank=SearchRank(contact_search_vector, contact_search_query),
                similarity=Greatest(TrigramSimilarity("email", query), TrigramSimilarity("phone", query)),
            )
            .exclude(is_anonymous=True)
            .filter(Q(rank__gte=0.3) | Q(similarity__gt=0.3))
        )

        return donors | contact_donors
