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
from localflavor.ro.ro_counties import COUNTIES_CHOICES

from donations.models.jobs import Job, JobDownloadError, JobStatusChoices
from donations.models.main import Donor, Ngo
from redirectioneaza.common.messaging import send_email

logger = logging.getLogger(__name__)


COUNTIES_CHOICES_REVERSED = {name: code for code, name in COUNTIES_CHOICES}


def download_donations_job(job_id: int = 0):
    try:
        job: Job = Job.objects.select_related("ngo").get(id=job_id)
    except Job.DoesNotExist:
        logger.error("Job with ID %d does not exist", job_id)
        return

    ngo: Ngo = job.ngo
    timestamp: datetime = timezone.now()
    donations: QuerySet[Donor] = Donor.current_year_signed.filter(ngo=ngo).order_by("-date_created").all()

    file_name = f"n{ngo.id:06d}__{datetime.strftime(timestamp, '%Y%m%d_%H%M')}.zip"

    with tempfile.TemporaryDirectory(prefix=f"rdr_zip_{job_id:06d}_") as tmp_dir_name:
        logger.info("Created temporary directory '%s'", tmp_dir_name)
        try:
            zip_path = _package_donations(tmp_dir_name, donations, ngo, file_name)
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


def _package_donations(tmp_dir_name: str, donations: QuerySet[Donor], ngo: Ngo, zip_name: str) -> str:
    logger.info("Processing %d donations for '%s'", len(donations), ngo.name)

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
                    logger.error("Could not download '%s'. Retries left %d.", source_url, retries_left)
                except Exception as e:
                    retries_left = 0
                    logger.error("Could not download '%s'. Exception %s", source_url, e)
                else:
                    with zip_archive.open(os.path.join("pdf", filename), mode="w", force_zip64=zip_64_flag) as handler:
                        handler.write(file_data)

                    zipped_files += 1
                    retries_left = 0

                    phone = _parse_phone(donation_object.phone)

                    donation_cnp: str = donation_object.get_cnp()
                    duplicate_cnp_idx: int = cnp_idx.get(donation_cnp, {}).get("index", 0)
                    if duplicate_cnp_idx == 0:
                        cnp_idx[donation_cnp] = {
                            "index": len(donations_data) + 1,
                            "has_duplicate": False,
                        }
                    else:
                        cnp_idx[donation_cnp]["has_duplicate"] = True

                    detailed_address: Dict = _get_address_details(donation_object)
                    donations_data.append(
                        {
                            # TODO: first name and last name have been swapped
                            # https://github.com/code4romania/redirectioneaza/issues/269
                            "last_name": donation_object.first_name,
                            "first_name": donation_object.last_name,
                            "initial": donation_object.initial,
                            "phone": phone,
                            "email": donation_object.email,
                            "cnp": donation_cnp,
                            "duplicate": duplicate_cnp_idx,
                            "county": donation_object.county,
                            "city": donation_object.city,
                            "full_address": detailed_address["full_address"],
                            "str": detailed_address["str"],
                            "nr": detailed_address["nr"],
                            "bl": detailed_address["bl"],
                            "sc": detailed_address["sc"],
                            "et": detailed_address["et"],
                            "ap": detailed_address["ap"],
                            "filename": filename,
                            "date": donation_object.date_created,
                            "duration": _parse_duration(donation_object.two_years),
                        }
                    )

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

        _generate_xml_files(ngo, zip_archive, zip_64_flag, zip_timestamp, cnp_idx)

    logger.info("Creating ZIP file for %d donations", zipped_files)

    return zip_path


def _parse_duration(donation_duration: bool) -> int:
    return 2 if donation_duration else 1


def _parse_phone(phone: str) -> str:
    if not phone:
        return ""

    return "".join([c for c in phone if c.isdigit()])


def _get_address_details(donation_object: Donor) -> Dict[str, str]:
    full_address: Dict = donation_object.get_address()

    full_address_prefix: str = f"jud. {donation_object.county}, loc. {donation_object.city}"
    full_address_string: str = f"{full_address_prefix}, {donation_object.address_to_string(full_address)}"

    address_details = {
        "full_address": full_address_string,
        "str": full_address.get("str", ""),
        "nr": full_address.get("nr", ""),
        "bl": full_address.get("bl", ""),
        "sc": full_address.get("sc", ""),
        "et": full_address.get("et", ""),
        "ap": full_address.get("ap", ""),
    }

    return address_details


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
    ngo: Ngo, zip_archive: ZipFile, zip_64_flag: bool, zip_timestamp: datetime, cnp_idx: Dict[str, Dict[str, Any]]
):
    if not cnp_idx or not ngo or not zip_archive:
        return

    ngo_donations: QuerySet[Donor] = Donor.current_year_signed.filter(ngo=ngo).order_by("-date_created")

    # if there are less than 2 * settings.DONATIONS_XML_LIMIT_PER_FILE donations
    # create a single XML file
    if ngo_donations.count() < 2 * settings.DONATIONS_XML_LIMIT_PER_FILE:
        xml_name: str = "d230.xml"
        _build_xml(ngo, ngo_donations, 1, xml_name, cnp_idx, zip_timestamp, zip_archive, zip_64_flag)

        return

    _generate_donations_by_county(cnp_idx, ngo, ngo_donations, zip_64_flag, zip_archive, zip_timestamp)


def _generate_donations_by_county(cnp_idx, ngo, ngo_donations, zip_64_flag, zip_archive, zip_timestamp):
    donations_limit: int = settings.DONATIONS_XML_LIMIT_PER_FILE

    number_of_donations_by_county: QuerySet[Tuple[str, int]] = (
        ngo_donations.values("county").annotate(count=Count("county")).order_by("count").values_list("county", "count")
    )

    xml_count: int = 1
    for current_county, current_county_count in number_of_donations_by_county:
        # if there are more than donations_limit donations for a county, split them into multiple files
        county_code: str = COUNTIES_CHOICES_REVERSED.get(current_county, f"S{current_county}").lower().replace(" ", "_")
        if current_county_count <= donations_limit:
            xml_name: str = f"d230_{county_code}.xml"

            county_donations: QuerySet[Donor] = ngo_donations.filter(county=current_county)
            _build_xml(ngo, county_donations, xml_count, xml_name, cnp_idx, zip_timestamp, zip_archive, zip_64_flag)
            xml_count += 1
        else:
            for i in range(math.ceil(current_county_count / donations_limit)):
                xml_name: str = f"d230_{county_code}_{xml_count:04}.xml"

                county_donations: QuerySet[Donor] = ngo_donations.filter(county=current_county)[:donations_limit]
                _build_xml(ngo, county_donations, xml_count, xml_name, cnp_idx, zip_timestamp, zip_archive, zip_64_flag)

                xml_count += 1


def _build_xml(
    ngo: Ngo,
    donations_batch: QuerySet[Donor],
    batch_count: int,
    xml_name: str,
    cnp_idx: Dict[str, Dict[str, Any]],
    zip_timestamp: datetime,
    zip_archive: ZipFile,
    zip_64_flag: bool,
):
    # 01. XML opening tag
    xml_str: str = """<?xml version="1.0" encoding="UTF-8"?>\n<form1>"""

    # 02. XML header
    xml_str += _build_xml_header(ngo, batch_count, zip_timestamp)

    # 03. XML body
    for donation_idx, donation in enumerate(donations_batch):
        # skip donations which have a duplicate CNP from the XML
        cnp = donation.get_cnp()
        if cnp in cnp_idx and cnp_idx[cnp]["has_duplicate"]:
            if not cnp_idx[cnp].get("skip", False):
                cnp_idx[cnp]["skip"] = True
            else:
                continue

        xml_str += _build_xml_donation_content(donation, donation_idx, ngo)

    # 04. XML closing tag
    xml_str += """</form1>"""

    # 05. XML cleanup
    xml_str = xml_str.replace("\n            ", "\n")
    xml_str = xml_str.replace("\n\n", "\n")

    with zip_archive.open(os.path.join("xml", xml_name), mode="w", force_zip64=zip_64_flag) as handler:
        handler.write(xml_str.encode())


def _clean_registration_number(cif: str) -> str:
    # The CIF should be added without the "RO" prefix
    cif: str = cif.upper()
    return cif if not cif.startswith("RO") else cif[2:]


def _build_xml_header(ngo, xml_idx, zip_timestamp) -> str:
    valid_registration_number: str = _clean_registration_number(ngo.registration_number)

    # noinspection HttpUrlsUsage
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
                    <cif>{valid_registration_number}</cif>
                    <formValid>FORMULAR NEVALIDAT</formValid>
                    <luna_r>12</luna_r>
                    <d_rec>0</d_rec>
                    <an_r>{zip_timestamp.year - 1}</an_r>
                </IdDoc>
                <imp>
                    <bifaI>
                        <rprI>0</rprI>
                    </bifaI>
                </imp>
                <z_tipPersoana>Rad2</z_tipPersoana>
                <z_denEntitate>{ngo.name}</z_denEntitate>
                <z_cifEntitate>{valid_registration_number}</z_cifEntitate>
                <z_ibanEntitate>{ngo.bank_account}</z_ibanEntitate>
                <nrDataB>
                    <nrD>{xml_idx}</nrD>
                    <dataD>{zip_timestamp.day:02}.{zip_timestamp.month:02}.{zip_timestamp.year}</dataD>
                    <denD>{ngo.name}</denD>
                    <cifD>{valid_registration_number}</cifD>
                    <adresaD>{ngo.address}</adresaD>
                    <ibanD>{ngo.bank_account}</ibanD>
                </nrDataB>
            """
    return xml_str


def _build_xml_donation_content(donation: Donor, donation_idx: int, ngo: Ngo):
    # TODO: first name and last name have been swapped
    # https://github.com/code4romania/redirectioneaza/issues/269

    # noinspection HttpUrlsUsage
    detailed_address: Dict = _get_address_details(donation)
    return f"""
                <contrib>
                    <nrCrt>
                        <nV>{donation_idx + 1}</nV>
                    </nrCrt>
                    <idCnt>
                        <nume>{donation.first_name.upper()}</nume>
                        <init>{donation.initial.upper()}</init>
                        <pren>{donation.last_name.upper()}</pren>
                        <cif_c>{donation.get_cnp()}</cif_c>
                        <adresa>{detailed_address["full_address"].upper()}</adresa>
                        <telefon>{_parse_phone(donation.phone)}</telefon>
                        <fax/>
                        <email>{donation.email}</email>
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
                                    <anDoi>{_parse_duration(donation.two_years)}</anDoi>
                                    <cifOJ>{_clean_registration_number(ngo.registration_number)}</cifOJ>
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
