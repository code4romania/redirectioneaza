from typing import Optional

from django.db.models import QuerySet

from donations.models.ngos import Cause


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
    def is_reused(cls, slug: str, form_pk: Optional[int] = None):
        ngo_form_queryset: QuerySet = Cause.objects.filter(slug=slug.lower())

        if form_pk:
            ngo_form_queryset = ngo_form_queryset.exclude(pk=form_pk)

        if ngo_form_queryset.exists():
            return True

        return False
