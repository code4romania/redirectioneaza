import json
from datetime import datetime
from functools import partial
from typing import Dict

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.common.models_hashing import hash_id_secret


def year_ngo_donor_directory_path(subdir: str, instance: "Donor", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/c-<cause.id>-<cause.hash>/<id>_<hash>_<filename>
    """
    timestamp = timezone.now()
    year = timestamp.date().year

    cause_pk = instance.cause.pk if instance.cause else 0
    cause_hash = hash_id_secret("cause", cause_pk)

    redirection_pk = instance.pk
    redirection_hash = hash_id_secret("donor", redirection_pk)

    return "/".join(
        [
            f"{subdir}",
            f"{year}",
            f"c-{cause_pk}-{cause_hash}",
            f"{redirection_pk}_{redirection_hash}_{filename}",
        ]
    )


class DonorSignedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(has_signed=True)


class DonorCurrentYearSignedManager(DonorSignedManager):
    def get_queryset(self):
        return super().get_queryset().filter(date_created__year=timezone.now().year)


class DonorCurrentYearManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(date_created__year=timezone.now().year)


class Donor(models.Model):
    INCOME_CHOICES = (
        ("wage", _("wage")),
        ("pension", _("pension")),
    )

    ngo = models.ForeignKey("Ngo", verbose_name=_("NGO"), on_delete=models.SET_NULL, db_index=True, null=True)
    cause = models.ForeignKey("Cause", verbose_name=_("cause"), on_delete=models.SET_NULL, db_index=True, null=True)

    l_name = models.CharField(
        verbose_name=_("last name"), blank=True, null=False, default="", max_length=100, db_index=True
    )
    f_name = models.CharField(
        verbose_name=_("first name"), blank=True, null=False, default="", max_length=100, db_index=True
    )
    initial = models.CharField(verbose_name=_("initials"), blank=True, null=False, default="", max_length=5)

    encrypted_cnp = models.TextField(verbose_name=_("CNP"), blank=True, null=False, default="")

    city = models.CharField(
        verbose_name=_("city"),
        blank=True,
        null=False,
        default="",
        max_length=100,
        db_index=True,
    )
    county = models.CharField(
        verbose_name=_("county"),
        blank=True,
        null=False,
        default="",
        max_length=100,
        db_index=True,
    )
    encrypted_address = models.TextField(verbose_name=_("address"), blank=True, null=False, default="")

    # originally: tel
    phone = models.CharField(
        verbose_name=_("telephone"),
        blank=True,
        null=False,
        default="",
        max_length=30,
        db_index=True,
    )
    email = models.EmailField(
        verbose_name=_("email"),
        blank=False,
        null=False,
        db_index=True,
    )

    # originally: "anonymous"
    is_anonymous = models.BooleanField(
        verbose_name=_("anonymous"),
        db_index=True,
        default=True,
        help_text=_("If the user would like the ngo to see the donation"),
    )
    anaf_gdpr = models.BooleanField(
        verbose_name=_("ANAF GDPR"),
        default=False,
        help_text=_("If the user agrees for ANAF to share their data with the NGO"),
    )

    # originally: "income"
    income_type = models.CharField(
        verbose_name=_("income type"),
        max_length=30,
        default="wage",
        blank=True,
        null=False,
        choices=INCOME_CHOICES,
    )

    two_years = models.BooleanField(
        verbose_name=_("two years"),
        default=False,
        help_text=_("If the user wants to donate for 2 years"),
    )

    geoip = models.JSONField(verbose_name=_("Geo IP"), blank=True, null=False, default=dict)

    filename = models.CharField(verbose_name=_("filename"), blank=True, null=False, default="", max_length=100)
    has_signed = models.BooleanField(verbose_name=_("has signed"), db_index=True, default=False)

    pdf_file = models.FileField(
        verbose_name=_("PDF file"),
        blank=True,
        null=False,
        upload_to=partial(year_ngo_donor_directory_path, "donation-forms"),
    )

    date_created = models.DateTimeField(
        verbose_name=_("date created"),
        db_index=True,
        auto_now_add=True,
    )

    objects = models.Manager()
    signed = DonorSignedManager()
    current_year = DonorCurrentYearManager()
    current_year_signed = DonorCurrentYearSignedManager()

    class Meta:
        verbose_name = _("donor")
        verbose_name_plural = _("donors")

    def __str__(self):
        return f"{self.cause} {self.date_created} {self.email}"

    def set_cnp(self, cnp: str):
        self.encrypted_cnp = self.encrypt_cnp(cnp)

    def get_cnp(self) -> str:
        if not self.encrypted_cnp:
            return ""

        return self.decrypt_cnp(self.encrypted_cnp)

    def set_address_helper(
        self,
        street_name: str,
        street_number: str,
        street_bl: str = "",
        street_sc: str = "",
        street_et: str = "",
        street_ap: str = "",
    ):
        address = {
            "str": street_name,
            "nr": street_number,
        }

        if street_bl:
            address["bl"] = street_bl
        if street_sc:
            address["sc"] = street_sc
        if street_et:
            address["et"] = street_et
        if street_ap:
            address["ap"] = street_ap

        self._set_address(address)

    def _set_address(self, address: dict):
        self.encrypted_address = self.encrypt_address(address)

    def get_address(self) -> Dict:
        return self.decrypt_address(self.encrypted_address)

    def get_address_string(self) -> str:
        address = self.get_address()
        return self.address_to_string(address)

    @staticmethod
    def address_to_string(address: Dict) -> str:
        street_name = address.get("str", "")
        street_number = address.get("nr", "")
        street_bl = address.get("bl", "")
        street_sc = address.get("sc", "")
        street_et = address.get("et", "")
        street_ap = address.get("ap", "")

        address_string = f"{street_name} {street_number}"
        if street_bl:
            address_string += f", bl. {street_bl}"
        if street_sc:
            address_string += f", sc. {street_sc}"
        if street_et:
            address_string += f", et. {street_et}"
        if street_ap:
            address_string += f", ap. {street_ap}"

        return address_string

    @property
    def donation_hash(self):
        if not self.pk:
            raise ValueError
        return hash_id_secret("donor", self.pk)

    @property
    def date_str(self):
        if not self.date_created:
            raise ValueError
        return datetime.strftime(self.date_created, "%Y%m%d")

    @property
    def form_url(self):
        if not self.pk:
            raise ValueError

        return reverse(
            "donor-download-link",
            kwargs={
                "donor_date_str": self.date_str,
                "donor_id": self.id,
                "donor_hash": self.donation_hash,
            },
        )

    @staticmethod
    def encrypt_cnp(cnp: str) -> str:
        return settings.FERNET_OBJECT.encrypt(cnp.encode()).decode()

    @staticmethod
    def decrypt_cnp(cnp: str) -> str:
        if not cnp:
            return cnp

        return settings.FERNET_OBJECT.decrypt(cnp.encode()).decode()

    @staticmethod
    def encrypt_address(address: Dict) -> str:
        return settings.FERNET_OBJECT.encrypt(json.dumps(address).encode()).decode()

    @staticmethod
    def decrypt_address(address: str) -> Dict:
        if not address:
            return {}

        return json.loads(settings.FERNET_OBJECT.decrypt(address.encode()).decode())
