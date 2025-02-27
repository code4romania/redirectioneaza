import datetime
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import Q, QuerySet
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ngettext_lazy
from django.views.generic import ListView

from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import Cause, Ngo


def get_was_last_job_recent(ngo: Optional[Ngo]) -> bool:
    if not ngo:
        return True

    now = timezone.now()
    last_ngo_job: Job = ngo.jobs.order_by("-date_created").first()

    if last_ngo_job:
        last_job_date = last_ngo_job.date_created
        last_job_status = last_ngo_job.status

        timedelta = datetime.timedelta(0)
        if last_job_status != JobStatusChoices.ERROR:
            timedelta = datetime.timedelta(minutes=settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES)

        if last_job_date > now - timedelta:
            return True

    return False


def get_time_between_retries() -> str:
    time_between_retries = settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES

    if time_between_retries >= 60:
        time_between_retries = time_between_retries // 60
        period_between_retries = ngettext_lazy(
            "%(time)d hour",
            "%(time)d hours",
            time_between_retries,
        ) % {"time": time_between_retries}
    else:
        period_between_retries = ngettext_lazy(
            "%(time)d minute",
            "%(time)d minutes",
            time_between_retries,
        ) % {"time": time_between_retries}

    return period_between_retries


def get_ngo_archive_download_status(ngo: Optional[Ngo]) -> Dict:
    last_job_was_recent = get_was_last_job_recent(ngo)
    context = {
        "last_job_was_recent": last_job_was_recent,
    }

    if not last_job_was_recent:
        return context

    context["period_between_retries"] = get_time_between_retries()

    return context


def get_is_over_donation_archival_limit() -> bool:
    if timezone.now().date() > settings.DONATIONS_LIMIT + datetime.timedelta(
        days=settings.TIMEDELTA_DONATIONS_LIMIT_DOWNLOAD_DAYS
    ):
        return True

    return False


def get_cause_response_item(cause: Cause) -> Dict:
    return {
        "name": cause.name,
        "url": reverse("twopercent", kwargs={"ngo_url": cause.slug}),
        "logo": cause.display_image.url if cause.display_image else None,
        "description": cause.description,
    }


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


class SearchMixin(ListView):
    def get_search_results(self, queryset: QuerySet, query: str, language_code: str) -> QuerySet:
        raise NotImplementedError("You must add your own logic for searching")

    def search(self) -> QuerySet:
        query: str = self.request.GET.get("q")

        if not query or len(query) < settings.SEARCH_QUERY_MIN_LENGTH:
            return self.queryset.all()

        language_code: str = settings.LANGUAGE_CODE
        if hasattr(self.request, "LANGUAGE_CODE") and self.request.LANGUAGE_CODE:
            language_code = self.request.LANGUAGE_CODE
        language_code = language_code.lower()

        return self.get_search_results(self.queryset, query, language_code)


class NgoSearchMixin(SearchMixin):
    @classmethod
    def get_search_results(cls, queryset: QuerySet, query: str, language_code: str) -> QuerySet:
        search_fields = ["name", "registration_number"]
        search_vector: SearchVector = ConfigureSearch.vector(search_fields, language_code)
        search_query: SearchQuery = ConfigureSearch.query(query, language_code)

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


class CauseSearchMixin(SearchMixin):
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
            .filter(Q(rank__gte=0.3) | Q(similarity__gt=0.3))
            .order_by("name")
            .distinct("name")
        )

        return causes


class NgoCauseMixedSearchMixin(SearchMixin):
    @classmethod
    def get_search_results(cls, queryset: QuerySet, query: str, language_code: str) -> QuerySet[Cause]:
        ngos = NgoSearchMixin.get_search_results(Ngo.active, query, language_code)
        ngos_causes = Cause.active.filter(ngo__in=ngos).distinct("name")

        searched_causes = CauseSearchMixin.get_search_results(queryset, query, language_code)

        return searched_causes | ngos_causes


def get_ngo_cause(slug: str) -> Tuple[Optional[Cause], Ngo]:
    #  XXX: [MULTI-FORM] This is a temporary solution to handle both causes and NGOs
    try:
        cause: Optional[Cause] = Cause.active.get(slug=slug)
        ngo: Ngo = cause.ngo
    except Cause.DoesNotExist:
        try:
            ngo: Ngo = Ngo.active.get(slug=slug)
            cause = ngo.causes.first()
        except Ngo.DoesNotExist:
            raise Http404

    return cause, ngo
