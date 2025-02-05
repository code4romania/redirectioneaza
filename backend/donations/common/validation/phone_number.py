from typing import Dict

import phonenumbers
from django.utils.translation import gettext_lazy as _
from phonenumbers.phonenumber import PhoneNumber


def validate_phone_number(raw_phone_number) -> Dict[str, str]:
    try:
        phone_number: PhoneNumber = phonenumbers.parse(raw_phone_number)
    except phonenumbers.NumberParseException:
        try:
            phone_number: PhoneNumber = phonenumbers.parse(raw_phone_number, region="RO")
        except phonenumbers.NumberParseException:
            return {
                "status": "error",
                "result": _("Invalid phone number"),
            }

    if not phonenumbers.is_valid_number(phone_number):
        return {
            "status": "error",
            "result": _("Invalid phone number"),
        }

    # Format the phone number in E.164 format (e.g. "+40 (72) 12-34-567" -> "+40721234567")
    normalized_phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
    return {
        "status": "success",
        "result": normalized_phone,
    }
