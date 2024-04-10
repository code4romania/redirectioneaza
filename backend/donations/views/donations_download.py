import csv
import io
import logging
import math
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict
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
    donations: QuerySet[Donor] = Donor.objects.filter(
        ngo=ngo,
        has_signed=True,
        date_created__gte=datetime(
            year=timestamp.year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timestamp.tzinfo
        ),
    ).all()

    file_name = datetime.strftime(timestamp, "%Y%m%d_%H%M") + f"__n{ngo.id:06d}.zip"

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


def _package_donations(tmp_dir_name: str, donations: QuerySet[Donor], ngo: Ngo):
    logger.info("Processing %d donations for '%s'", len(donations), ngo.name)

    zip_timestamp = timezone.now()
    zip_name = datetime.strftime(zip_timestamp, "%Y%m%d_%H%M") + f"__n{ngo.id:06d}.zip"
    zip_path = Path(tmp_dir_name) / zip_name

    zip_64_flag = len(donations) > 4000

    zipped_files: int = 0

    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED, compresslevel=1) as zip_archive:
        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output, quoting=csv.QUOTE_ALL)
        csv_writer.writerow(
            [
                _("last name"),
                _("first name"),
                _("initial"),
                _("CNP"),
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

        donations_data: list[dict] = []
        donation: Donor

        for donation in donations:
            donations_data.append({})

            source_url = _get_pdf_url(donation)

            if not source_url:
                continue

            donation_timestamp = donation.date_created or timezone.now()
            filename = datetime.strftime(donation_timestamp, "%Y%m%d_%H%M") + f"__d{donation.id:06d}.pdf"

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
                    with zip_archive.open(filename, mode="w", force_zip64=zip_64_flag) as handler:
                        handler.write(file_data)

                    zipped_files += 1
                    retries_left = 0

                    full_address: Dict = donation.get_address()
                    donations_data[-1] = {
                        "last_name": donation.last_name,
                        "first_name": donation.first_name,
                        "initial": donation.initial,
                        "phone": donation.phone,
                        "email": donation.email,
                        "cnp": donation.get_cnp(),
                        "county": donation.county,
                        "city": donation.city,
                        "full_address": f"jud. {donation.county}, loc. {donation.city}, "
                        + donation.address_to_string(full_address),
                        "str": full_address.get("str", ""),
                        "nr": full_address.get("nr", ""),
                        "bl": full_address.get("bl", ""),
                        "sc": full_address.get("sc", ""),
                        "et": full_address.get("et", ""),
                        "ap": full_address.get("ap", ""),
                        "filename": filename,
                        "date": donation.date_created,
                        "duration": 2 if donation.two_years else 1,
                    }

                    csv_writer.writerow(
                        [
                            donations_data[-1]["last_name"],
                            donations_data[-1]["first_name"],
                            donations_data[-1]["initial"],
                            donations_data[-1]["cnp"],
                            donations_data[-1]["phone"],
                            donations_data[-1]["email"],
                            donations_data[-1]["county"],
                            donations_data[-1]["city"],
                            donations_data[-1]["full_address"],
                            donations_data[-1]["str"],
                            donations_data[-1]["nr"],
                            donations_data[-1]["bl"],
                            donations_data[-1]["sc"],
                            donations_data[-1]["et"],
                            donations_data[-1]["ap"],
                            donations_data[-1]["filename"],
                            donations_data[-1]["date"],
                            donations_data[-1]["duration"],
                        ]
                    )

        # Attach a CSV file with all donor data
        logger.info("Attaching the CSV to the ZIP")
        with zip_archive.open("index.csv", mode="w", force_zip64=zip_64_flag) as handler:
            handler.write(csv_output.getvalue().encode())

        # Attach XML files with data for up to 1000 donors each
        logger.info("Attaching the XMLs to the ZIP")
        for xml_idx in range(1, math.ceil(len(donations_data) / 1000) + 1):
            # The XML header content
            xml_str = f"""
                <?xml version="1.0" encoding="UTF-8"?>
                <form1>
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
                        <an_r>2023</an_r>
                    </IdDoc>
            """

            donation_idx = 0
            for donation_data in donations_data[(xml_idx - 1) * 1000 : xml_idx * 1000]:
                donation_idx += 1
                # The XML donation content
                xml_str += f"""
                    <contrib>
                        <nrCrt>
                            <nV>{donation_idx}</nV>
                        </nrCrt>
                        <idCnt>
                            <nume>{donation_data["last_name"]}</nume>
                            <init>{donation_data["initial"]}</init>
                            <pren>{donation_data["first_name"]}</pren>
                            <cif_c>{donation_data["cnp"]}</cif_c>
                            <adresa>{donation_data["full_address"]}</adresa>
                            <telefon>{donation_data["phone"]}</telefon>
                            <fax/>
                            <email>{donation_data["email"]}</email>
                        </idCnt>
                        <s15>
                            <date>
                                <nrCrt>
                                    <nV>{donation_idx}</nV>
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
                                        <anDoi>{1 if donation_data["duration"] > 1 else 0}</anDoi>
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

            # The XML footer content
            xml_str += f"""
                <footer>
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
                </footer>
            </form1>
            """
            with zip_archive.open(f"index_{xml_idx:04}.xml", mode="w", force_zip64=zip_64_flag) as handler:
                handler.write(xml_str.encode())

    logger.info("Creating ZIP file for %d donations", zipped_files)

    return zip_path


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


def _announce_done(job: Job):
    send_email(
        subject=_("Documents ready for download"),
        to_emails=[job.ngo.email],
        text_template="email/zipped_forms/zipped_forms.txt",
        html_template="email/zipped_forms/zipped_forms.html",
        context={"link": reverse("admin-download-link", kwargs={"job_id": job.id})},
    )
