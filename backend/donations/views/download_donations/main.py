import codecs
import csv
import io
import logging
import math
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Tuple
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from django.conf import settings
from django.core.files import File
from django.db.models import Count, QuerySet
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.common.validation.phone_number import clean_phone_number
from donations.models.donors import Donor
from donations.models.jobs import Job, JobDownloadError, JobStatusChoices
from donations.models.ngos import Cause
from donations.views.download_donations.build_xml import add_xml_to_zip
from redirectioneaza.common.app_url import build_uri
from redirectioneaza.common.clean import duration_flag_to_int, normalize_text_alnum
from redirectioneaza.common.messaging import extend_email_context, send_email

logger = logging.getLogger(__name__)


def download_donations_job(job_id: int = 0):
    try:
        job: Job = Job.objects.select_related("cause").get(id=job_id)
    except Job.DoesNotExist:
        logger.error("Job with ID %d does not exist", job_id)
        return

    cause: Cause = job.cause

    timestamp: datetime = timezone.now()
    donations: QuerySet[Donor] = Donor.current_year_signed.filter(cause=cause).order_by("-date_created").all()

    number_of_donations = donations.count()
    job.number_of_donations = number_of_donations

    if number_of_donations == 0:
        job.status = JobStatusChoices.ERROR
        job.save()

        return

    file_name = f"n{cause.id:06d}__{datetime.strftime(timestamp, '%Y%m%d_%H%M')}.zip"

    with tempfile.TemporaryDirectory(prefix=f"rdr_zip_{job_id:06d}_") as tmp_dir_name:
        logger.info("Created temporary directory '%s'", tmp_dir_name)
        try:
            zip_path = _package_donations(tmp_dir_name, donations, cause, file_name)
            with open(zip_path, "rb") as f:
                job.zip.save(file_name, File(f), save=False)
            job.status = JobStatusChoices.DONE
            job.save()
        except Exception as e:
            logger.error("Error processing job %d: %s", job_id, e)
            job.status = JobStatusChoices.ERROR
            job.save()
            return

    mail_context = {
        "action_url": build_uri(reverse("my-organization:archive-download-link", kwargs={"job_id": job.id})),
    }
    mail_context.update(extend_email_context())

    send_email(
        subject=_("Documents ready for download"),
        to_emails=[job.cause.ngo.email],
        html_template="emails/ngo/download-archive/main.html",
        text_template="emails/ngo/download-archive/main.txt",
        context=mail_context,
    )


def _package_donations(tmp_dir_name: str, donations: QuerySet[Donor], cause: Cause, zip_name: str) -> str:
    logger.info("Processing %d donations for '%s'", len(donations), cause.name)

    zip_timestamp: datetime = timezone.now()
    zip_path: str = os.path.join(tmp_dir_name, zip_name)

    zip_64_flag: bool = len(donations) > 4000

    zipped_files: int = 0

    cnp_idx: Dict[str, Dict[str, Any]] = {}
    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED, compresslevel=1) as zip_archive:
        # Attach a TXT help file
        logger.info("Attaching the TXT help file to the ZIP")
        with zip_archive.open("DESCRIERE.html", mode="w", force_zip64=zip_64_flag) as handler:
            help_text = render_to_string("DESCRIERE.html", context={})
            handler.write(help_text.encode())

        # record a CNP first appearance 1-based-index in the data list of donations
        donations_data: List[Dict] = []

        donation_object: Donor
        for donation_object in donations:
            source_url = _get_pdf_url(donation_object)

            if not source_url:
                continue

            donation_timestamp: datetime = donation_object.date_created
            filename = f"{datetime.strftime(donation_timestamp, '%Y%m%d_%H%M')}__d{donation_object.id:06d}.pdf"

            retries_left = 2
            while retries_left > 0:
                try:
                    file_data = _download_file(source_url)
                except JobDownloadError:
                    retries_left -= 1
                    logger.error(
                        "Could not download '%s'. Retries left %d.",
                        source_url,
                        retries_left,
                    )
                except Exception as e:
                    retries_left = 0
                    logger.error("Could not download '%s'. Exception %s", source_url, e)
                else:
                    with zip_archive.open(os.path.join("pdf", filename), mode="w", force_zip64=zip_64_flag) as handler:
                        handler.write(file_data)

                    zipped_files += 1
                    retries_left = 0

                    phone = clean_phone_number(donation_object.phone)

                    donation_cnp: str = donation_object.get_cnp()
                    duplicate_cnp_idx: int = cnp_idx.get(donation_cnp, {}).get("index", 0)
                    if duplicate_cnp_idx == 0:
                        cnp_idx[donation_cnp] = {
                            "index": len(donations_data) + 1,
                            "has_duplicate": False,
                        }
                    else:
                        cnp_idx[donation_cnp]["has_duplicate"] = True

                    detailed_address: Dict = donation_object.get_address(include_full=True)
                    county = (
                        donation_object.county
                        if len(str(donation_object.county)) > 1
                        else f"Sector {donation_object.county}"
                    )
                    donations_data.append(
                        {
                            "last_name": donation_object.l_name,
                            "first_name": donation_object.f_name,
                            "initial": donation_object.initial,
                            "phone": phone,
                            "email": donation_object.email,
                            "cnp": donation_cnp,
                            "duplicate": duplicate_cnp_idx,
                            "county": county,
                            "city": donation_object.city,
                            "full_address": detailed_address.get("full_address", ""),
                            "str": detailed_address.get("str", ""),
                            "nr": detailed_address.get("nr", ""),
                            "bl": detailed_address.get("bl", ""),
                            "sc": detailed_address.get("sc", ""),
                            "et": detailed_address.get("et", ""),
                            "ap": detailed_address.get("ap", ""),
                            "filename": filename,
                            "date": donation_object.date_created,
                            "duration": duration_flag_to_int(donation_object.two_years),
                        }
                    )

        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output, dialect=csv.excel)
        csv_writer.writerow(
            [
                _("no."),
                _("last name"),
                _("first name"),
                _("initial"),
                _("CNP"),
                _("duplicate"),
                _("phone"),
                _("email"),
                _("county"),
                _("city"),
                _("full address"),
                _("street name"),
                _("street number"),
                _("building"),
                _("entrance"),
                _("floor"),
                _("apartment"),
                _("filename"),
                _("date"),
                _("duration"),
            ]
        )
        for index, donation_csv in enumerate(donations_data):
            csv_writer.writerow(
                [
                    index + 1,
                    donation_csv["last_name"],
                    donation_csv["first_name"],
                    donation_csv["initial"],
                    donation_csv["cnp"],
                    donation_csv["duplicate"],
                    donation_csv["phone"],
                    donation_csv["email"],
                    donation_csv["county"],
                    donation_csv["city"],
                    donation_csv["full_address"],
                    donation_csv["str"],
                    donation_csv["nr"],
                    donation_csv["bl"],
                    donation_csv["sc"],
                    donation_csv["et"],
                    donation_csv["ap"],
                    donation_csv["filename"],
                    donation_csv["date"],
                    donation_csv["duration"],
                ]
            )

        # Create the CSV file as a temporary file
        with tempfile.TemporaryFile() as fp:
            fp.write(codecs.BOM_UTF8)
            fp.write(csv_output.getvalue().encode())

            # Attach a CSV file with all donor data
            logger.info("Attaching the CSV to the ZIP")
            with zip_archive.open("index.csv", mode="w", force_zip64=zip_64_flag) as handler:
                fp.seek(0)
                handler.write(fp.read())

        _generate_xml_files(cause, zip_archive, zip_64_flag, zip_timestamp, cnp_idx)

    logger.info("Creating ZIP file for %d donations", zipped_files)

    return zip_path


def _get_pdf_url(donation: Donor) -> str:
    if donation.pdf_file:
        source_url = donation.pdf_file.url
    else:
        source_url = ""

    if not source_url:
        logger.info("Donation #%d has no PDF URL", donation.id)
    else:
        logger.debug("Donation #%d PDF URL: '%s'", donation.id, source_url)

    return source_url


def _download_file(source_url: str) -> bytes:
    if not source_url.startswith("https://"):
        media_root = "/".join(settings.MEDIA_ROOT.split("/")[:-1])
        with open(media_root + source_url, "rb") as f:
            return f.read()

    if not source_url:
        raise ValueError("source_url is empty")

    response = requests.get(source_url)

    if response.status_code != 200:
        raise JobDownloadError

    return response.content


def _generate_xml_files(
    cause: Cause,
    zip_archive: ZipFile,
    zip_64_flag: bool,
    zip_timestamp: datetime,
    cnp_idx: Dict[str, Dict[str, Any]],
):
    if not cnp_idx or not cause or not zip_archive:
        return

    ngo_donations: QuerySet[Donor] = Donor.current_year_signed.filter(cause=cause).order_by("-date_created")

    # if there are less than 2 * settings.DONATIONS_XML_LIMIT_PER_FILE donations
    # create a single XML file
    if ngo_donations.count() < 2 * settings.DONATIONS_XML_LIMIT_PER_FILE:
        xml_name: str = "d230.xml"
        add_xml_to_zip(
            cause,
            ngo_donations,
            1,
            xml_name,
            cnp_idx,
            zip_timestamp,
            zip_archive,
            zip_64_flag,
        )

        return

    _generate_donations_by_county(cnp_idx, cause, ngo_donations, zip_64_flag, zip_archive, zip_timestamp)


def _generate_donations_by_county(cnp_idx, cause: Cause, ngo_donations, zip_64_flag, zip_archive, zip_timestamp):
    donations_limit: int = settings.DONATIONS_XML_LIMIT_PER_FILE

    number_of_donations_by_county: QuerySet[Tuple[str, int]] = (
        ngo_donations.values("county").annotate(count=Count("county")).order_by("count").values_list("county", "count")
    )

    xml_count: int = 1
    for current_county, current_county_count in number_of_donations_by_county:
        # if there are more than donations_limit donations for a county, split them into multiple files
        clean_county_name = normalize_text_alnum(current_county)
        county_code = settings.COUNTIES_CHOICES_WITH_SECTORS_REVERSED_CLEAN.get(
            clean_county_name, f"sector{clean_county_name}"
        )
        county_code = county_code.lower().replace(" ", "_")

        if current_county_count <= donations_limit:
            xml_name: str = f"d230_{county_code}.xml"

            county_donations: QuerySet[Donor] = ngo_donations.filter(county=current_county)
            add_xml_to_zip(
                cause,
                county_donations,
                xml_count,
                xml_name,
                cnp_idx,
                zip_timestamp,
                zip_archive,
                zip_64_flag,
            )
            xml_count += 1
        else:
            for i in range(math.ceil(current_county_count / donations_limit)):
                xml_name: str = f"d230_{county_code}_{xml_count:04}.xml"

                county_donations: QuerySet[Donor] = ngo_donations.filter(county=current_county)[
                    i * donations_limit : (i + 1) * donations_limit
                ]
                add_xml_to_zip(
                    cause,
                    county_donations,
                    xml_count,
                    xml_name,
                    cnp_idx,
                    zip_timestamp,
                    zip_archive,
                    zip_64_flag,
                )

                xml_count += 1
