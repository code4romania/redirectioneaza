import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_CHARACTERS_REGEX = r"[^RO0-9]"
REGISTRATION_NUMBER_REGEX = r"^([A-Z]{2}|)\d{2,10}$"
REGISTRATION_NUMBER_REGEX_SANS_VAT = r"^\d{2,10}$"
REGISTRATION_NUMBER_REGEX_WITH_VAT = r"^[A-Z]{2}\d{2,10}$"


def extract_vat_id(registration_number: str) -> dict[str, str]:
    """
    Extract the VAT ID and the registration number from a valid registration number.
    :param registration_number:
        A registration number that may or may not contain a VAT ID.
        The registration number must have a valid format.
    :return: A dictionary containing the VAT ID and the registration number.
        {
            "vat_id": "RO",
            "registration_number": "1234567890",
        }
    """

    result = {
        "vat_id": "",
        "registration_number": registration_number,
    }

    if re.match(REGISTRATION_NUMBER_REGEX_SANS_VAT, registration_number):
        return result

    result["vat_id"] = registration_number[:2]
    result["registration_number"] = registration_number[2:]

    return result


def clean_registration_number(registration_number: str) -> str | None:
    """
    Clean up a registration number by uppercasing the string, then removing any whitespace or forbidden characters.
    :param registration_number: The registration number to clean.
    :return: The cleaned registration number.
    """
    if re.match(REGISTRATION_NUMBER_REGEX, registration_number):
        return registration_number

    # uppercase the string and strip of any whitespace
    registration_number = registration_number.upper().strip()

    # remove all the whitespace
    registration_number = re.sub(r"\s+", "", registration_number)

    # remove any forbidden characters
    registration_number = re.sub(ALLOWED_CHARACTERS_REGEX, "", registration_number)

    return registration_number


def ngo_id_number_validator(value):
    """
    Validate a registration number for an NGO.
    :param value: The registration number to validate.
    :return: None
    """

    reg_num: str = "".join([char for char in value.upper() if char.isalnum()])

    if reg_num == len(reg_num) * "0":
        raise ValidationError(_("The ID number cannot be all zeros"))

    if not re.match(REGISTRATION_NUMBER_REGEX, reg_num):
        raise ValidationError(_("The ID number format is not valid"))

    if re.match(REGISTRATION_NUMBER_REGEX_WITH_VAT, reg_num):
        reg_num = value[2:]

    if not reg_num.isdigit():
        raise ValidationError(_("The ID number must contain only digits"))

    if 2 > len(reg_num) or len(reg_num) > 10:
        raise ValidationError(_("The ID number must be between 2 and 10 digits long"))

    if not settings.ENABLE_FULL_VALIDATION_CUI:
        return

    control_key: str = "753217532"

    reversed_key: list[int] = [int(digit) for digit in control_key[::-1]]
    reversed_cif: list[int] = [int(digit) for digit in reg_num[::-1]]

    cif_control_digit: int = reversed_cif.pop(0)

    cif_key_pairs: tuple[int, ...] = tuple(
        cif_digit * key_digit for cif_digit, key_digit in zip(reversed_cif, reversed_key)
    )
    control_result: int = sum(cif_key_pairs) * 10 % 11

    if control_result == cif_control_digit:
        return
    elif control_result == 10 and cif_control_digit == 0:
        return

    raise ValidationError(_("The ID number is not valid"))
