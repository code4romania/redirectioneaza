import datetime
from typing import Dict, Optional, Tuple

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ngettext_lazy
from donations.models.jobs import Job, JobStatusChoices
from donations.models.ngos import Cause, Ngo


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


def archive_job_was_recent(job_status: str, job_created: datetime) -> bool:
    if job_status == JobStatusChoices.ERROR:
        return False

    timedelta = datetime.timedelta(minutes=settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES)

    if job_created > timezone.now() - timedelta:
        return True

    return False


def has_recent_archive_job(cause: Cause) -> bool:
    last_cause_archive: Job = cause.jobs.order_by("-date_created").first()

    if not last_cause_archive:
        return False

    return archive_job_was_recent(last_cause_archive.status, last_cause_archive.date_created)


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


def has_archive_generation_deadline_passed() -> bool:
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


def get_ngo_cause(slug: str) -> Tuple[Optional[Cause], Ngo]:
    #  XXX: [MULTI-FORM] This is a temporary solution to handle both causes and NGOs
    try:
        cause: Optional[Cause] = Cause.nonprivate_active.get(slug=slug)
        ngo: Ngo = cause.ngo
    except Cause.DoesNotExist:
        try:
            ngo: Ngo = Ngo.active.get(slug=slug)
            cause = Cause.main.filter(ngo=ngo).first()
        except (Cause.DoesNotExist, Ngo.DoesNotExist):
            raise Http404

    return cause, ngo
