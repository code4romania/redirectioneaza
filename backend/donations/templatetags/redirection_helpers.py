from django import template
from django.utils import dateparse

from donations.views.common.misc import archive_job_was_recent

register = template.Library()


@register.filter
def job_was_recent(job: dict) -> bool:
    """
    Check if the job was created recently.
    """
    if not job:
        return False

    job_created: str = job["date_created"]
    job_created_date = dateparse.parse_datetime(job_created)

    return archive_job_was_recent(job["status"], job_created_date)
