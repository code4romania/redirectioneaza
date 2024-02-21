import io
import logging
from datetime import datetime
from zipfile import ZipFile

import requests
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.models.jobs import Job, JobStatusChoices, JobDownloadError
from donations.models.main import Donor, Ngo
from redirectioneaza.common.messaging import send_email


logger = logging.getLogger(__name__)


def download_donations_job(job_id: int = 0):
    try:
        job: Job = Job.objects.select_related("ngo").get(id=job_id)
    except Job.DoesNotExist:
        logger.error("Job with ID %d does not exist", job_id)
        return

    ngo: Ngo = job.ngo
    ts = timezone.now()
    donations: QuerySet[Donor] = Donor.objects.filter(
        ngo=ngo,
        has_signed=True,
        date_created__gte=datetime(year=ts.year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=ts.tzinfo),
    ).all()

    try:
        zip_byte_stream: io.BytesIO = _package_donations(donations, job, ngo)
        job.zip.save(f"{ngo.name}.zip", zip_byte_stream, save=False)
        job.status = JobStatusChoices.DONE
        job.save()
    except Exception as e:
        logger.error("Error processing job %d: %s", job_id, e)
        job.status = JobStatusChoices.ERROR
        job.save()
        return

    _announce_done(job)


def _package_donations(donations: QuerySet[Donor], job: Job, ngo: Ngo) -> io.BytesIO:
    zip_byte_stream = io.BytesIO()

    with ZipFile(zip_byte_stream, mode="w", compresslevel=1) as zip_archive:
        logger.info("Processing %d donations for '%s'", len(donations), ngo.name)
        for donation in donations:
            source_url: str  # Current donation's PDF file URL

            # The 'pdf_file' property has priority over the old 'pdf_url' one
            if donation.pdf_file:
                source_url = donation.pdf_file.url
            elif donation.pdf_url:
                source_url = donation.pdf_url
            else:
                source_url = ""

            if not source_url:
                logger.info("Donation #%d has no PDF URL", donation.id)
                continue
            else:
                logger.info("Donation #%d PDF URL: '%s'", donation.id, source_url)

            retries_left = 2
            while retries_left > 0:
                try:
                    pdf_content: bytes = _download_file(source_url)
                except JobDownloadError:
                    retries_left -= 1
                    logger.error("Could not download '%s'. Retries left %d.", source_url, retries_left)
                except Exception as e:
                    retries_left = 0
                    logger.error("Could not download '%s'. Exception %s", source_url, e)
                else:
                    retries_left = 0
                    donation_timestamp = donation.date_created or timezone.now()
                    filename = datetime.strftime(donation_timestamp, "%Y%m%d_%H%M") + f"__{donation.id}.pdf"
                    with zip_archive.open(filename, "w") as archive_file:
                        archive_file.write(pdf_content)

    return zip_byte_stream


def _download_file(source_url: str) -> bytes:
    if not source_url.startswith("https://"):
        media_root = "/".join(settings.MEDIA_ROOT.split("/")[:-1])
        with open(media_root + source_url, "rb") as f:
            return f.read()

    if not source_url:
        raise ValueError("source_url is empty")

    response = requests.get(source_url, stream=True)

    if response.status_code != 200:
        raise JobDownloadError
    else:
        return response.content


def _announce_done(job: Job):
    send_email(
        subject=_("Documents ready for download"),
        to_emails=[job.ngo.email],
        text_template="email/zipped_forms/zipped_forms.txt",
        html_template="email/zipped_forms/zipped_forms.html",
        context={"link": job.zip.url},
    )
