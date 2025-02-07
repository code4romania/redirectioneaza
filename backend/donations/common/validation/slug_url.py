import unicodedata

from django.db.models import QuerySet

from donations.models.ngos import Ngo


def replace_spaces_with_dashes(s: str) -> str:
    """Replace spaces with dashes in a string."""

    return s.replace(" ", "-")


def strip_accents(s: str) -> str:
    """Remove accents from a string."""

    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def remove_unwanted_characters(s: str) -> str:
    """Remove all characters from a string except for letters, numbers, and dashes."""

    return "".join(c for c in s if c.isalnum() or c == "-")


def clean_slug(slug: str) -> str:
    slug = slug.lower()
    slug = replace_spaces_with_dashes(slug)
    slug = strip_accents(slug)
    slug = remove_unwanted_characters(slug)

    return slug


class NgoSlugValidator:
    ngo_url_block_list = (
        "",
        "TERMENI",
        "admin",
        "allauth",
        "api",
        "asociatia",
        "asociatii",
        "confirmare-cont",
        "cont-nou",
        "contul-meu",
        "cron",
        "date-cont",
        "despre",
        "doilasuta",
        "donatie",
        "download",
        "email-demo",
        "faq",
        "forgot",
        "health",
        "login",
        "logout",
        "media",
        "ngos",
        "nota-de-informare",
        "ong",
        "organizatia",
        "organizatia-mea",
        "organizatie",
        "organizatii",
        "password",
        "pentru-ong-uri",
        "politica",
        "recuperare-parola",
        "semnatura",
        "static",
        "succes",
        "redirectioneaza",
        "termene-si-conditii",
        "termeni",
        "tinymce",
        "validare-cont",
        "verify",
    )

    @classmethod
    def is_blocked(cls, slug: str):
        if slug.lower() in cls.ngo_url_block_list:
            return True

        return False

    @classmethod
    def is_reused(cls, slug: str, ngo_pk: int):
        ngo_queryset: QuerySet[Ngo] = Ngo.objects

        ngo_queryset = ngo_queryset.exclude(pk=ngo_pk)

        if ngo_queryset.filter(slug=slug.lower()).exists():
            return True

        return False
