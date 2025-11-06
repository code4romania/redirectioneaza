import re
import string
import unicodedata

from django.utils.text import slugify


def strip_accents(source: str) -> str:
    """
    Source - https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
    Posted by oefe
    Retrieved 2025-11-06, License - CC BY-SA 3.0
    """
    return "".join(c for c in unicodedata.normalize("NFD", source) if unicodedata.category(c) != "Mn")


def remove_unwanted_characters(s: str) -> str:
    """Remove all characters from a string except for letters, numbers, and dashes."""

    return "".join(c for c in s if c.isalnum() or c == "-")


def clean_slug(slug: str) -> str:
    """Slugify the string but also remove underscores and other unwanted characters."""
    slug = slugify(slug)
    slug = remove_unwanted_characters(slug)

    return slug


def unicode_to_ascii(text: str) -> str:
    """
    Convert text with diacritics to ASCII.
    """

    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def duration_flag_to_int(donation_duration: bool) -> int:
    """
    Convert the donation duration boolean to an integer.
    """

    return 2 if donation_duration else 1


def anaf_gdpr_flag_to_int(anaf_gdpr: bool) -> int:
    """
    Convert the ANAF GDPR boolean to an integer.
    """

    return 1 if anaf_gdpr else 0


def clean_text_email(email: str) -> str:
    """
    Keep only a minimal subset of the valid email characters.
    Note: Plus-addressing and other characteristics beyond the most basic will not be supported.
    """

    email_regex = r"^[a-zA-Z0-9_\.\-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]+$"

    if not email or not re.match(email_regex, email):
        return ""

    return email


def clean_text_alphabet(text: str, *, allow_spaces: bool = False) -> str:
    """
    Keep only alphabetic characters and, optionally spaces.
    """

    new_text: str = ""

    for c in text:
        if c.isalpha():
            new_text += c
        elif allow_spaces:
            new_text += " "

    return new_text


def clean_text_numbers(text: str, *, allow_spaces: bool = False) -> str:
    """
    Keep only numeric characters and, optionally spaces.
    """

    new_text: str = ""

    for c in text:
        if c.isnumeric():
            new_text += c
        elif allow_spaces:
            new_text += " "

    return new_text


def clean_text_alnum(text: str, *, allow_spaces: bool = False) -> str:
    """
    Keep only alphanumeric characters and, optionally spaces.
    """

    new_text: str = ""

    for c in text:
        if c.isalnum():
            new_text += c
        elif allow_spaces:
            new_text += " "

    return new_text


def clean_text_custom(text: str) -> str:
    """
    ANAF has a custom list of characters allowed in the XML: [A-Z, a-z, 0-9, ",", ".", "-", " "]
    Note: The list sometimes includes "&" but it's not consistent, so we're not including it here.
    """

    ANAF_CUSTOM_LIST = string.ascii_letters + string.digits + "," + "." + "-" + " "

    return "".join([c for c in text if c in ANAF_CUSTOM_LIST])


def normalize_text_alnum(text) -> str:
    """
    Normalize text to lowercase, remove diacritics, and keep only alphanumeric characters.
    """

    text = text.lower()
    text = unicode_to_ascii(text)
    text = "".join([c if c.isalnum() else "" for c in text])

    return text
