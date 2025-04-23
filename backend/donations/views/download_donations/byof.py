import csv
import io
import logging
from typing import Annotated, Dict, List, Optional
from xml.etree.ElementTree import Element, ElementTree

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone

from donations.models.byof import OwnFormsUpload

from pydantic import BaseModel, EmailStr, StringConstraints, ValidationError

from donations.views.download_donations.common import (
    XMLNS_DETAILS,
    build_borderou_data_from_raw,
    build_btn_doc,
    build_id_doc_from_raw,
    build_imp,
    new_xml_element,
    build_donor_raw,
)
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class EmailEmptyAllowedStr(EmailStr, str):
    @classmethod
    def _validate(cls, input_value: str) -> str:
        if input_value == "":
            return input_value
        return super()._validate(input_value)


class DonorModel(BaseModel):
    # noinspection PyTypeHints
    cnp: Annotated[
        str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=13, max_length=13, pattern=r"^\d{13}$")
    ]
    # noinspection PyTypeHints
    first_name: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True)]
    # noinspection PyTypeHints
    last_name: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True)]
    initial: Optional[str] = Annotated[
        str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=1, pattern=r"^[a-zA-Z]$")
    ]

    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: EmailEmptyAllowedStr = ""

    anaf_gdpr: Optional[str] = "0"
    period: Optional[str] = "1"


def generate_xml_from_external_data(own_upload_id):
    """
    Generate an archive for the given NGO and file.
    :param own_upload_id: The ID of the uploaded data
    :return: The file of the generated XML
    """

    try:
        own_upload = OwnFormsUpload.objects.select_related("ngo").get(pk=own_upload_id)
    except OwnFormsUpload.DoesNotExist:
        return {"error": "Cannot find the uploaded data"}

    ngo_name = own_upload.ngo.name
    ngo_cui = own_upload.ngo.registration_number
    ngo_address = own_upload.ngo.address
    ngo_locality = own_upload.ngo.locality
    ngo_county = own_upload.ngo.county

    try:
        parsed_data = parse_file_data(own_upload.uploaded_data.file)
    except ValueError as e:
        return {"error": str(e)}

    xml_element_tree: ElementTree = build_xml_from_file_data(
        data=parsed_data,
        iban=own_upload.bank_account,
        ngo_name=ngo_name,
        ngo_cui=ngo_cui,
        ngo_address=ngo_address,
        ngo_locality=ngo_locality,
        ngo_county=ngo_county,
    )

    return xml_element_tree


def parse_file_data(file: InMemoryUploadedFile) -> List[DonorModel]:
    """
    Transform the CSV file to raw data.
    :param file: The CSV file path
    :return: A list of dictionaries containing the information of donors
    """
    read_file = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(read_file))

    header_check = _check_csv_header(reader)
    if check_error := header_check.get("error"):
        raise ValueError(check_error)

    errors = []
    parsed_data: List[DonorModel] = []
    for line in reader:
        try:
            donor = DonorModel(
                cnp=line["cnp"],
                first_name=line["prenume"],
                last_name=line["nume"],
                initial=line.get("initiala", ""),
                address=line.get("adresa", ""),
                phone=line.get("telefon", ""),
                email=line.get("email", ""),
                anaf_gdpr=line.get("anaf_gdpr", "0"),
                period=line.get("perioada", "1"),
            )
            parsed_data.append(donor)
        except ValidationError as e:
            errors.append({"line_num": reader.line_num - 1, "line": str(line), "errors": e.errors()})
        except Exception as e:
            raise ValueError(
                _("Invalid data in line %(line_num)d %(line)s. Error: %(error)s")
                % {
                    "line_num": reader.line_num,
                    "line": str(line),
                    "error": str(e),
                }
            )
    if errors:
        parsed_errors = _parse_pydantic_errors(errors)
        raise ValueError(_("Errors found in the file: %(errors)s") % {"errors": parsed_errors})

    return parsed_data


def _parse_pydantic_errors(pydantic_errors):
    parsed_errors: List[str] = []
    for pydantic_error in pydantic_errors:
        line_errors = pydantic_error["errors"]

        for line_error in line_errors:
            errored_fields = ", ".join(line_error["loc"])

            pretty_error = _(
                "Error at line #%(line_num)d %(line_start)s. "
                "Please check fields %(fields)s for the following errors: '%(error)s'"
            ) % {
                "line_num": pydantic_error["line_num"],
                "line_start": pydantic_error["line"][:6],
                "fields": errored_fields,
                "error": _associate_error_message_to_translated_message(line_error["msg"]),
            }
            parsed_errors.append(pretty_error)

    return parsed_errors


def _associate_error_message_to_translated_message(error_message: str) -> str:
    if error_message in ("String should have at least 13 characters", "String should have at most 13 characters"):
        return _("The field should have 13 characters")
    elif "value is not a valid email address" in error_message:
        return _("The field should be a valid email address")
    else:
        logger.error(f"Unhandled error message: {error_message}")
        return _("The field is invalid")


def _check_csv_header(reader: csv.DictReader) -> Dict[str, str]:
    mandatory_header_items = {"cnp", "prenume", "nume"}
    valid_header_items = mandatory_header_items.union(
        {"initiala", "adresa", "telefon", "email", "anaf_gdpr", "perioada"}
    )

    reader_header = set(reader.fieldnames)

    if missing_header_items := mandatory_header_items.difference(reader_header):
        return {"error": _("Missing mandatory items in header: %(missing)s") % {"missing": missing_header_items}}

    if invalid_header_items := reader_header.difference(valid_header_items):
        return {"error": _("Invalid items in header: %(invalid)s") % {"invalid": invalid_header_items}}

    return {"success": "Header is valid"}


def build_xml_from_file_data(
    data: List[DonorModel],
    iban: str,
    ngo_name: str,
    ngo_cui: str,
    ngo_address: str,
    ngo_locality: str,
    ngo_county: str,
) -> ElementTree:
    timestamp = timezone.now()

    xml = Element("form1")

    xml.append(build_btn_doc())
    xml.append(Element("semnatura", XMLNS_DETAILS))
    xml.append(Element("Title", XMLNS_DETAILS))
    xml.append(build_id_doc_from_raw(ngo_cui, timestamp))
    xml.append(build_imp())

    xml.append(new_xml_element(tag="z_tipPersoana", text="Rad2"))
    xml.append(new_xml_element(tag="z_denEntitate", text=ngo_name, clean="alnums"))
    xml.append(new_xml_element(tag="z_cifEntitate", text=ngo_cui, clean="numbers"))
    xml.append(new_xml_element(tag="z_ibanEntitate", text=iban, clean="alnum"))

    xml.append(
        build_borderou_data_from_raw(
            xml_index=1,
            timestamp=timestamp,
            bank_account=iban,
            ngo_name=ngo_name,
            ngo_registration_number=ngo_cui,
            ngo_address=ngo_address,
            ngo_locality=ngo_locality,
            ngo_county=ngo_county,
        )
    )

    for index, donor in enumerate(data):
        xml.append(
            build_donor_raw(
                index=index,
                ngo_cui=ngo_cui,
                ngo_name=ngo_name,
                bank_account=iban,
                donor_cnp=donor.cnp,
                donor_first_name=donor.first_name,
                donor_last_name=donor.last_name,
                donor_initial=donor.initial,
                donor_address=donor.address,
                donor_phone=donor.phone,
                donor_email=donor.email,
                donor_anaf_gdpr=donor.anaf_gdpr,
                donor_period=donor.period,
            )
        )

    return ElementTree(xml)
