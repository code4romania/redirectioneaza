from typing import Dict

import phonenumbers
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from phonenumbers.phonenumber import PhoneNumber


def validate_phone_number(raw_phone_number) -> Dict[str, str]:
    if raw_phone_number.startswith("+"):
        try:
            phone_number: PhoneNumber = phonenumbers.parse(raw_phone_number)
        except phonenumbers.NumberParseException as e:
            if e.error_type == phonenumbers.NumberParseException.INVALID_COUNTRY_CODE:
                return {
                    "status": "error",
                    "result": _("Invalid country code"),
                }

            return {
                "status": "error",
                "result": _("Unknown phone number format"),
            }
    else:
        try:
            phone_number: PhoneNumber = phonenumbers.parse(raw_phone_number, region="RO")
        except phonenumbers.NumberParseException:
            return {
                "status": "error",
                "result": _("Invalid phone number"),
            }

    if settings.ENABLE_FULL_VALIDATION_PHONE and not phonenumbers.is_valid_number(phone_number):
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
