import csv
import io
import logging
from typing import Annotated
from xml.etree.ElementTree import Element, ElementTree

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, EmailStr, StringConstraints, ValidationError

from donations.models.byof import OwnFormsStatusChoices, OwnFormsUpload
from donations.views.download_donations.common import (
    XMLNS_DETAILS,
    build_borderou_data_from_raw,
    build_btn_doc,
    build_donor_raw,
    build_id_doc_from_raw,
    build_imp,
    new_xml_element,
)

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
    initial: str | None = Annotated[
        str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=2, pattern=r"^[a-zA-Z]$")
    ]

    address: str | None = ""
    phone: str | None = ""
    email: EmailEmptyAllowedStr = ""

    anaf_gdpr: str | None = "0"
    period: str | None = "1"


def handle_external_data_processing(own_upload_id: int) -> dict | None:
    try:
        own_upload = OwnFormsUpload.objects.select_related("ngo").get(pk=own_upload_id)
    except OwnFormsUpload.DoesNotExist:
        return {"error": _("Cannot find the uploaded data")}

    own_upload.status = OwnFormsStatusChoices.VALIDATING
    own_upload.save()

    with own_upload.uploaded_data.open() as file:
        read_file = decode_readfile(file, one_line=True)
        reader = csv.DictReader(io.StringIO(read_file))

        header_check = _check_csv_header(reader)
        if check_error := header_check.get("error"):
            own_upload.status = OwnFormsStatusChoices.FAILED
            own_upload.result_text = check_error
            own_upload.save()
            return {"error": check_error}

        own_upload.items_count = sum([1 for i in file.readlines() if i.strip()])  # already read the first line
        own_upload.status = OwnFormsStatusChoices.PROCESSING
        own_upload.save()

    result = generate_xml_from_external_data(own_upload)

    if result.get("error"):
        own_upload.result_text = result["error"]
        own_upload.status = OwnFormsStatusChoices.FAILED
        own_upload.save()
        return {"error": result["error"]}

    etree: ElementTree = result.get("data")

    # Write to a BytesIO buffer
    buffer = io.BytesIO()
    etree.write(buffer, encoding="utf-8", xml_declaration=True)

    # Get the content from the buffer
    xml_content = buffer.getvalue()

    # Wrap in a ContentFile for Django
    xml_file = ContentFile(xml_content)

    # Save to FileField
    own_upload.result_data.save("data.xml", xml_file, save=False)
    own_upload.status = OwnFormsStatusChoices.SUCCESS
    own_upload.save()

    return None


def generate_xml_from_external_data(own_upload: OwnFormsUpload) -> dict[str, str | ElementTree | None]:
    """
    Generate an archive for the given NGO and file.
    :param own_upload: The uploaded data
    :return: The file of the generated XML
    """

    ngo_name = own_upload.ngo.name
    ngo_cui = own_upload.ngo.registration_number
    ngo_address = own_upload.ngo.address
    ngo_locality = own_upload.ngo.locality
    ngo_county = own_upload.ngo.county

    try:
        parsed_data = parse_file_data(own_upload.uploaded_data.open())
    except ValueError as e:
        return {"error": str(e), "data": None}

    xml_element_tree: ElementTree = build_xml_from_file_data(
        data=parsed_data,
        iban=own_upload.bank_account,
        ngo_name=ngo_name,
        ngo_cui=ngo_cui,
        ngo_address=ngo_address,
        ngo_locality=ngo_locality,
        ngo_county=ngo_county,
    )

    return {"error": None, "data": xml_element_tree}


def decode_readfile(input_file, *, one_line=False) -> str:
    # TODO: Try to optimize/simplify this
    readfile = input_file.readline() if one_line else input_file.read()

    # Try to decode the file as utf-8 with BOM - common for Microsoft Office
    # We have to do this before trying plain utf-8 because utf-8 with BOM is a subset of utf-8
    try:
        # Deepcopy the readfile to avoid modifying the original bytes
        read_file = readfile.decode("utf-8-sig")
    except UnicodeDecodeError:
        input_file.seek(0)
    else:
        return read_file

    # If utf-8 with BOM fails, try with plain utf-8
    try:
        # Try to decode the file as utf-8 with BOM
        readfile = input_file.readline() if one_line else input_file.read()
        read_file = readfile.decode("utf-8")
    except UnicodeDecodeError:
        input_file.seek(0)
    else:
        return read_file

    # If utf-8 fails, try cp1252 - common for Microsoft Windows
    try:
        readfile = input_file.readline() if one_line else input_file.read()
        read_file = readfile.decode("cp1252")
    except UnicodeDecodeError:
        input_file.seek(0)
    else:
        return read_file

    raise ValueError(_("The file is not in a valid format."))


def parse_file_data(file) -> list[DonorModel]:
    """
    Transform the CSV file to raw data.
    :param file: The CSV file path
    :return: A list of dictionaries containing the information of donors
    """

    read_file = decode_readfile(file)

    reader = csv.DictReader(io.StringIO(read_file))

    header_check = _check_csv_header(reader)
    if check_error := header_check.get("error"):
        raise ValueError(check_error)

    errors = []
    parsed_data: list[DonorModel] = []
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
    parsed_errors: list[str] = []
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


def _check_csv_header(reader: csv.DictReader) -> dict[str, str]:
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
    data: list[DonorModel],
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
