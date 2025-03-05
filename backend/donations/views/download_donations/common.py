import re
from typing import Dict

from donations.models.donors import Donor


def parse_duration(donation_duration: bool) -> int:
    return 2 if donation_duration else 1


def get_address_details(donation_object: Donor) -> Dict[str, str]:
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


def parse_email_for_anaf(email: str) -> str:
    email_regex = r"^[a-zA-Z0-9_\.\-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]+$"

    if not email or not re.match(email_regex, email):
        return ""

    return email
