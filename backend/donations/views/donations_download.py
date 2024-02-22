import io
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from django.conf import settings
from django.core.files import File
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.models.jobs import Job, JobStatusChoices, JobDownloadError
from donations.models.main import Donor, Ngo
from redirectioneaza.common.messaging import send_email


# Run the entire download & archive process in memory (5k documents use about 4GB of RAM)
IN_MEMORY = False


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

    if IN_MEMORY:
        try:
            zip_byte_stream: io.BytesIO = _memory_package_donations(donations, job, ngo)
            job.zip.save(f"{ngo.name}.zip", zip_byte_stream, save=False)
            job.status = JobStatusChoices.DONE
            job.save()
        except Exception as e:
            logger.error("Error processing job %d: %s", job_id, e)
            job.status = JobStatusChoices.ERROR
            job.save()
            return

    else:
        with tempfile.TemporaryDirectory(prefix=f"rdr_zip_{job_id:06d}_") as tmpdirname:
            logger.info("Created temporary directory '%s'", tmpdirname)
            try:
                zip_path = _package_donations(tmpdirname, donations, job, ngo)
                file_name = f"{ngo.id:04f}_{ngo.name}.zip"
                with open(zip_path, "rb") as f:
                    job.zip.save(file_name, File(f), save=False)
                job.status = JobStatusChoices.DONE
                job.save()
            except Exception as e:
                logger.error("Error processing job %d: %s", job_id, e)
                job.status = JobStatusChoices.ERROR
                job.save()
                return

    _announce_done(job)


def _get_pdf_url(donation: Donor) -> str:
    # The 'pdf_file' property has priority over the old 'pdf_url' one
    if donation.pdf_file:
        source_url = donation.pdf_file.url
    elif donation.pdf_url:
        source_url = donation.pdf_url
    else:
        source_url = ""

    if not source_url:
        logger.info("Donation #%d has no PDF URL", donation.id)
    else:
        logger.info("Donation #%d PDF URL: '%s'", donation.id, source_url)

    return source_url


def _package_donations(tmpdirname: str, donations: QuerySet[Donor], job: Job, ngo: Ngo):
    logger.info("Processing %d donations for '%s'", len(donations), ngo.name)

    zip_timestamp = timezone.now()
    zip_name = datetime.strftime(zip_timestamp, "%Y%m%d_%H%M") + f"__{ngo.id}.zip"
    zip_path = Path(tmpdirname) / zip_name

    zip_64_flag = len(donations) > 4000

    zipped_files: int = 0
    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED, compresslevel=9) as zip_archive:
        for donation in donations:
            source_url = _get_pdf_url(donation)

            if not source_url:
                continue

            donation_timestamp = donation.date_created or timezone.now()
            filename = datetime.strftime(donation_timestamp, "%Y%m%d_%H%M") + f"__{donation.id}.pdf"
            destination_path = Path(tmpdirname) / filename

            retries_left = 2
            while retries_left > 0:
                try:
                    file_data = _download_file(destination_path, source_url)
                except JobDownloadError:
                    retries_left -= 1
                    logger.error("Could not download '%s'. Retries left %d.", source_url, retries_left)
                except Exception as e:
                    retries_left = 0
                    logger.error("Could not download '%s'. Exception %s", source_url, e)
                else:
                    with zip_archive.open(filename, mode="w", force_zip64=zip_64_flag) as handler:
                        handler.write(file_data)

                    zipped_files += 1
                    retries_left = 0

    logger.info("Creating ZIP file for %d donations", zipped_files)

    return zip_path


def _download_file(destination_path, source_url: str):
    if not source_url.startswith("https://"):
        media_root = "/".join(settings.MEDIA_ROOT.split("/")[:-1])
        with open(media_root + source_url, "rb") as f:
            return f.read()
        #     with open(destination_path, "wb") as w:
        #         w.write(f.read())
        # return

    if not source_url:
        raise ValueError("source_url is empty")

    response = requests.get(source_url)

    if response.status_code != 200:
        raise JobDownloadError

    return response.content
    # with open(destination_path, "wb") as w:
    #     w.write(response.content)


def _memory_package_donations(donations: QuerySet[Donor], job: Job, ngo: Ngo) -> io.BytesIO:
    zip_byte_stream = io.BytesIO()

    with ZipFile(zip_byte_stream, mode="w", compresslevel=1) as zip_archive:
        logger.info("Processing in memory %d donations for '%s'", len(donations), ngo.name)
        for donation in donations:
            source_url = _get_pdf_url(donation)

            if not source_url:
                continue

            retries_left = 2
            while retries_left > 0:
                try:
                    pdf_content: bytes = _memory_download_file(source_url)
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


def _memory_download_file(source_url: str) -> bytes:
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
