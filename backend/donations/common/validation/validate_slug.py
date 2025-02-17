from django.db.models import QuerySet

from donations.models.ngos import Ngo, NgoForm


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
    def is_reused(cls, slug: str, form_pk: int):
        ngo_form_queryset: QuerySet = NgoForm.objects.exclude(pk=form_pk).filter(slug=slug.lower())

        if ngo_form_queryset.exists():
            return True

        return False

    @classmethod
    def is_reused_by_ngo(cls, slug: str, ngo_pk: int):
        ngo_queryset: QuerySet[Ngo] = Ngo.objects

        ngo_queryset = ngo_queryset.exclude(pk=ngo_pk)

        if ngo_queryset.filter(slug=slug.lower()).exists():
            return True

        return False
