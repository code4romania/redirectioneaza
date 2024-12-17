import datetime
from typing import Dict

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import Q, QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ngettext_lazy
from django.views.generic import ListView

from ..models.jobs import Job, JobStatusChoices
from ..models.ngos import Ngo


def get_was_last_job_recent(ngo: Ngo) -> bool:
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


def get_ngo_archive_download_status(ngo: Ngo):
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
