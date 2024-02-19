import io
import logging
from zipfile import ZipFile

import requests
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from donations.models.jobs import Job, JobStatusChoices, JobDownloadError
from donations.models.main import Donor, Ngo
from redirectioneaza.common.messaging import send_email

logger = logging.getLogger(__name__)


def download_donations_job(job_id: int):
    if not Job.objects.filter(id=job_id).exists():
        logger.error(f"Job with ID {job_id} does not exist")
        return

    job: Job = Job.objects.get(id=job_id)
    ngo: Ngo = job.ngo

    donations: QuerySet[Donor] = Donor.objects.filter(ngo=ngo, has_signed=True).all()

    try:
        zip_byte_stream: io.BytesIO = _package_donations(donations, job, ngo)
        job.zip.save(f"{ngo.name}.zip", zip_byte_stream.getvalue(), save=False)
        job.status = JobStatusChoices.DONE
        job.save()
    except Exception as e:
        logger.error(f"Error while processing job {job_id}: {e}")
        job.status = JobStatusChoices.ERROR
        job.save()
        return

    # TODO: is there anything left over to delete?

    _announce_done(job)


def _package_donations(donations, job, ngo) -> io.BytesIO:
    zip_byte_stream = io.BytesIO()
    with ZipFile(zip_byte_stream, mode="w") as zip_archive:
        for donation in donations:
            source_url: str  # The URL to the filled-in form file

            # The pdf_file property has priority over the old pdf_url one
            if donation.pdf_file:
                source_url = donation.pdf_file.url
            elif donation.pdf_url:
                source_url = donation.pdf_url
                logger.info(f"Downloading {donation.pdf_url}")
            else:
                source_url = ""

            try:
                pdf_content: bytes = _download_file(source_url)
            except JobDownloadError:
                # TODO: Handle the pdf download error. Maybe postpone the entire job?
                logger.warn(f"Could not download {source_url}")
            else:
                with zip_archive.open(donation.pdf_file.name, "w") as archive_file:
                    archive_file.write(pdf_content)

    # TODO: remove the files from the filesystem at the end

    return zip_byte_stream


def _download_file(pdf_url: str) -> bytes:
    if not pdf_url:
        raise ValueError("pdf_url is empty")

    # TODO: Should google URLs be treated differently than AWS ones?
    # if "googleapis" in pdf_url:
    #     return requests.get(pdf_url).content

    response = requests.get(pdf_url, stream=True).content
    if response.status_code != 200:
        raise JobDownloadError
    else:
        return response


def _announce_done(job: Job):
    send_email(
        subject=_("Documents ready for download"),
        to_emails=[job.ngo.email],
        text_template="email/zipped_forms/zipped_forms.txt",
        html_template="email/zipped_forms/zipped_forms.html",
        context={"link": job.zip.url},
    )
