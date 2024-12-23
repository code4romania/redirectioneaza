from typing import Dict

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import Q, QuerySet
from django.urls import reverse
from django.views.generic import ListView

from ..models.ngos import Ngo


def get_ngo_response_item(ngo) -> Dict:
    return {
        "name": ngo.name,
        "url": reverse("twopercent", kwargs={"ngo_url": ngo.slug}),
        "logo": ngo.logo.url if ngo.logo else None,
        "active_region": ngo.active_region,
        "description": ngo.description,
    }


class SearchMixin(ListView):
    def _configure_search_query(self, query: str, language_code: str) -> SearchQuery:
        if language_code == "ro":
            return SearchQuery(query, config="romanian_unaccent")

        return SearchQuery(query)

    def _configure_search_vector(self, language_code: str) -> SearchVector:
        if language_code == "ro":
            return SearchVector("name", weight="A", config="romanian_unaccent")

        return SearchVector("name", weight="A")

    def search(self, queryset: QuerySet) -> QuerySet:
        query: str = self.request.GET.get("q")

        if not query:
            return queryset.all()

        language_code: str = settings.LANGUAGE_CODE
        if hasattr(self.request, "LANGUAGE_CODE") and self.request.LANGUAGE_CODE:
            language_code = self.request.LANGUAGE_CODE
        language_code = language_code.lower()

        search_vector: SearchVector = self._configure_search_vector(language_code)
        search_query: SearchQuery = self._configure_search_query(query, language_code)

        ngos: QuerySet[Ngo] = (
            queryset.annotate(
                rank=SearchRank(search_vector, search_query),
                similarity=TrigramSimilarity("name", query),
            )
            .filter(Q(rank__gte=0.3) | Q(similarity__gt=0.3))
            .order_by("name")
            .distinct("name")
        )

        return ngos
