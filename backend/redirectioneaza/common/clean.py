import re
import string


def duration_flag_to_int(donation_duration: bool) -> int:
    return 2 if donation_duration else 1


def clean_text_email(email: str) -> str:
    email_regex = r"^[a-zA-Z0-9_\.\-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]+$"

    if not email or not re.match(email_regex, email):
        return ""

    return email


def clean_text_alphabet(text: str, *, allow_spaces: bool = False) -> str:
    new_text: str = ""

    for c in text:
        if c.isalpha():
            new_text += c
        elif allow_spaces:
            new_text += " "

    return new_text


def clean_text_numbers(text: str, *, allow_spaces: bool = False) -> str:
    new_text: str = ""

    for c in text:
        if c.isnumeric():
            new_text += c
        elif allow_spaces:
            new_text += " "

    return new_text


def clean_text_alnum(text: str, *, allow_spaces: bool = False) -> str:
    new_text: str = ""

    for c in text:
        if c.isalnum():
            new_text += c
        elif allow_spaces:
            new_text += " "

    return new_text


def clean_text_custom(text: str) -> str:
    ANAF_CUSTOM_LIST = string.ascii_letters + string.digits + "," + "." + "-" + " "

    return "".join([c for c in text if c in ANAF_CUSTOM_LIST])
