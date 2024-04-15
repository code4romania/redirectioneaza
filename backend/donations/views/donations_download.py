import csv
import io
import logging
import math
import os
import tempfile
from datetime import datetime
from typing import Dict, List
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from django.conf import settings
from django.core.files import File
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.models.jobs import Job, JobDownloadError, JobStatusChoices
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
    timestamp = timezone.now()
    donations: QuerySet[Donor] = (
        Donor.objects.filter(
            ngo=ngo,
            has_signed=True,
            date_created__gte=datetime(
                year=timestamp.year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timestamp.tzinfo
            ),
        )
        .order_by("-date_created")
        .all()
    )

    file_name = f"{datetime.strftime(timestamp, '%Y%m%d_%H%M')}__n{ngo.id:06d}.zip"

    with tempfile.TemporaryDirectory(prefix=f"rdr_zip_{job_id:06d}_") as tmp_dir_name:
        logger.info("Created temporary directory '%s'", tmp_dir_name)
        try:
            zip_path = _package_donations(tmp_dir_name, donations, ngo)
            with open(zip_path, "rb") as f:
                job.zip.save(file_name, File(f), save=False)
            job.status = JobStatusChoices.DONE
            job.save()
        except Exception as e:
            logger.error("Error processing job %d: %s", job_id, e)
            job.status = JobStatusChoices.ERROR
            job.save()
            return

    send_email(
        subject=_("Documents ready for download"),
        to_emails=[job.ngo.email],
        text_template="email/zipped_forms/zipped_forms.txt",
        html_template="email/zipped_forms/zipped_forms.html",
        context={"link": reverse("admin-download-link", kwargs={"job_id": job.id})},
    )


def _package_donations(tmp_dir_name: str, donations: QuerySet[Donor], ngo: Ngo):
    logger.info("Processing %d donations for '%s'", len(donations), ngo.name)

    zip_timestamp: datetime = timezone.now()
    zip_name: str = datetime.strftime(zip_timestamp, "%Y%m%d_%H%M") + f"__n{ngo.id:06d}.zip"
    zip_path: str = os.path.join(tmp_dir_name, zip_name)

    zip_64_flag: bool = len(donations) > 4000

    zipped_files: int = 0

    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED, compresslevel=1) as zip_archive:
        cnp_idx: dict[str, int] = {}  # record a CNP first appearance 1-based-index in the donations data list
        donations_data: List[Dict] = []

        donation_object: Donor
        for donation_object in donations:
            donations_data.append({})

            source_url = _get_pdf_url(donation_object)

            if not source_url:
                continue

            donation_timestamp = donation_object.date_created or timezone.now()
            filename = datetime.strftime(donation_timestamp, "%Y%m%d_%H%M") + f"__d{donation_object.id:06d}.pdf"

            retries_left = 2
            while retries_left > 0:
                try:
                    file_data = _download_file(source_url)
                except JobDownloadError:
                    retries_left -= 1
                    logger.error("Could not download '%s'. Retries left %d.", source_url, retries_left)
                except Exception as e:
                    retries_left = 0
                    logger.error("Could not download '%s'. Exception %s", source_url, e)
                else:
                    with zip_archive.open(os.path.join("pdf", filename), mode="w", force_zip64=zip_64_flag) as handler:
                        handler.write(file_data)

                    zipped_files += 1
                    retries_left = 0

                    phone = "".join([c for c in donation_object.phone if c.isdigit()])

                    donation_cnp: str = donation_object.get_cnp()
                    duplicate_cnp_idx: int = cnp_idx.get(donation_cnp, 0)
                    if duplicate_cnp_idx == 0:
                        cnp_idx[donation_cnp] = len(donations_data)

                    full_address: Dict = donation_object.get_address()
                    donations_data[-1] = {
                        "last_name": donation_object.last_name,
                        "first_name": donation_object.first_name,
                        "initial": donation_object.initial,
                        "phone": phone,
                        "email": donation_object.email,
                        "cnp": donation_cnp,
                        "duplicate": duplicate_cnp_idx,
                        "county": donation_object.county,
                        "city": donation_object.city,
                        "full_address": f"jud. {donation_object.county}, loc. {donation_object.city}, "
                        + donation_object.address_to_string(full_address),
                        "str": full_address.get("str", ""),
                        "nr": full_address.get("nr", ""),
                        "bl": full_address.get("bl", ""),
                        "sc": full_address.get("sc", ""),
                        "et": full_address.get("et", ""),
                        "ap": full_address.get("ap", ""),
                        "filename": filename,
                        "date": donation_object.date_created,
                        "duration": 2 if donation_object.two_years else 1,
                    }

        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output, quoting=csv.QUOTE_ALL)
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

        # Attach a CSV file with all donor data
        logger.info("Attaching the CSV to the ZIP")
        with zip_archive.open("index.csv", mode="w", force_zip64=zip_64_flag) as handler:
            handler.write(csv_output.getvalue().encode())

        _generate_xml_files(donations_data, ngo, zip_archive, zip_64_flag, zip_timestamp)

    logger.info("Creating ZIP file for %d donations", zipped_files)

    return zip_path


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


def _download_file(source_url: str):
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
    donations_data: List[Dict], ngo: Ngo, zip_archive: ZipFile, zip_64_flag: bool, zip_timestamp: datetime
):
    if not donations_data or not ngo or not zip_archive:
        return

    donations_data: List[Dict] = list(reversed(donations_data))

    previous_year: int = zip_timestamp.year - 1
    donations_per_file: int = settings.DONATIONS_XML_LIMIT_PER_FILE

    # Attach XML files with data for up to DONATIONS_XML_LIMIT_PER_FILE donors each
    logger.info("Attaching the XMLs to the ZIP")
    for xml_idx in range(1, math.ceil(len(donations_data) / donations_per_file) + 1):  # 1-based-index
        xml_str = _build_xml(donations_data, donations_per_file, ngo, previous_year, xml_idx, zip_timestamp)

        with zip_archive.open(
            os.path.join("xml", f"index_{xml_idx:04}.xml"), mode="w", force_zip64=zip_64_flag
        ) as handler:
            handler.write(xml_str.encode())


def _build_xml(donations_data, donations_per_file, ngo, previous_year, xml_idx, zip_timestamp):
    xml_str: str = """<?xml version="1.0" encoding="UTF-8"?>\n<form1>"""

    xml_str += _build_xml_header(ngo, previous_year, xml_idx, zip_timestamp)

    donations_slice: List[Dict] = donations_data[(xml_idx - 1) * donations_per_file : xml_idx * donations_per_file]
    for donation_idx, donation in enumerate(donations_slice):
        # skip donations which have a duplicate CNP from the XML
        if donation["duplicate"]:
            continue

        xml_str = _build_xml_donation_content(donation, donation_idx, ngo, xml_str)

    xml_str += """</form1>"""

    xml_str = xml_str.replace("\n            ", "\n")
    xml_str = xml_str.replace("\n\n", "\n")

    return xml_str


def _build_xml_header(ngo, previous_year, xml_idx, zip_timestamp) -> str:
    xml_str = f"""
                <btnDoc>
                    <btnSalt/>
                    <btnWebService/>
                    <info>
                        <help xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:dataNode="dataGroup"/>
                    </info>
                </btnDoc>
                <semnatura xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:dataNode="dataGroup"/>
                <Title xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:dataNode="dataGroup"/>
                <IdDoc>
                    <universalCode>B230_A1.0.8</universalCode>
                    <totalPlata_A/>
                    <cif>{ngo.registration_number}</cif>
                    <formValid>FORMULAR NEVALIDAT</formValid>
                    <luna_r>12</luna_r>
                    <d_rec>0</d_rec>
                    <an_r>{previous_year}</an_r>
                </IdDoc>
                <imp>
                    <bifaI>
                        <rprI>0</rprI>
                    </bifaI>
                </imp>
                <z_tipPersoana>Rad2</z_tipPersoana>
                <z_denEntitate>{ngo.name}</z_denEntitate>
                <z_cifEntitate>{ngo.registration_number}</z_cifEntitate>
                <z_ibanEntitate>{ngo.bank_account}</z_ibanEntitate>
                <nrDataB>
                    <nrD>{xml_idx}</nrD>
                    <dataD>{zip_timestamp.day:02}.{zip_timestamp.month:02}.{zip_timestamp.year}</dataD>
                    <denD>{ngo.name}</denD>
                    <cifD>{ngo.registration_number}</cifD>
                    <adresaD>{ngo.address}</adresaD>
                    <ibanD>{ngo.bank_account}</ibanD>
                </nrDataB>
            """
    return xml_str


def _build_xml_donation_content(donation, donation_idx, ngo, xml_str):
    xml_str += f"""
                <contrib>
                    <nrCrt>
                        <nV>{donation_idx + 1}</nV>
                    </nrCrt>
                    <idCnt>
                        <nume>{donation["last_name"].upper()}</nume>
                        <init>{donation["initial"].upper()}</init>
                        <pren>{donation["first_name"].upper()}</pren>
                        <cif_c>{donation["cnp"]}</cif_c>
                        <adresa>{donation["full_address"].upper()}</adresa>
                        <telefon>{donation['phone']}</telefon>
                        <fax/>
                        <email>{donation['email'].upper()}</email>
                    </idCnt>
                    <s15>
                        <date>
                            <nrCrt>
                                <nV>1</nV>
                            </nrCrt>
                            <optiuneSuma>
                                <slct>
                                    <ent>1</ent>
                                    <brs>0</brs>
                                </slct>
                            </optiuneSuma>
                            <brs>
                                <Gap xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:dataNode="dataGroup"/>
                                <idEnt>
                                    <nrDataC>
                                        <nrD/>
                                        <dataD/>
                                    </nrDataC>
                                    <nrDataP>
                                        <nrD/>
                                        <dataD/>
                                        <venitB/>
                                    </nrDataP>
                                </idEnt>
                            </brs>
                            <ent>
                                <Gap xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:dataNode="dataGroup"/>
                                <idEnt>
                                    <anDoi>{donation["duration"]}</anDoi>
                                    <cifOJ>{ngo.registration_number}</cifOJ>
                                    <denOJ>{ngo.name}</denOJ>
                                    <ibanNp>{ngo.bank_account}</ibanNp>
                                    <prc>3.50</prc>
                                    <venitB/>
                                </idEnt>
                            </ent>
                        </date>
                    </s15>
                </contrib>
            """

    return xml_str
