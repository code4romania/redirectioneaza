import hashlib
import json
import logging
from datetime import datetime
from functools import partial
from typing import Dict, List, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

ALL_NGOS_CACHE_KEY = "ALL_NGOS"
ALL_NGO_IDS_CACHE_KEY = "ALL_NGO_IDS"
FRONTPAGE_NGOS_KEY = "FRONTPAGE_NGOS"

logger = logging.getLogger(__name__)


def select_public_storage():
    return storages["public"]


def hash_id_secret(prefix: str, pk: int) -> str:
    # noinspection InsecureHash
    return hashlib.sha1(f"{prefix}-{pk}-{settings.SECRET_KEY}".encode()).hexdigest()[:10]


def ngo_directory_path(subdir: str, instance: "Ngo", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/ngo-<id>-<hash>/<filename>
    """
    return "{0}/ngo-{1}-{2}/{3}".format(subdir, instance.pk, hash_id_secret("ngo", instance.pk), filename)


def year_ngo_directory_path(subdir: str, instance: "Ngo", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/ngo-<id>-<hash>/<filename>
    """
    timestamp = timezone.now()
    return "{0}/{1}/ngo-{2}-{3}/{4}".format(
        subdir, timestamp.date().year, instance.pk, hash_id_secret("ngo", instance.pk), filename
    )


def year_ngo_donor_directory_path(subdir: str, instance: "Donor", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/ngo-<ngo.id>-<ngo.hash>/<id>_<hash>_<filename>
    """
    timestamp = timezone.now()
    return "{0}/{1}/ngo-{2}-{3}/{4}_{5}_{6}".format(
        subdir,
        timestamp.date().year,
        instance.ngo.pk if instance.ngo else 0,
        hash_id_secret("ngo", instance.ngo.pk if instance.ngo else 0),
        instance.pk,
        hash_id_secret("donor", instance.pk),
        filename,
    )


def ngo_slug_validator(value):
    valid_slug_sample: str = "organizatia-de-exemplu"
    error_message = _("%(value)s is not a valid identifier. The identifier must look like %(sample)s") % {
        "value": value,
        "sample": valid_slug_sample,
    }

    if not value.islower():
        raise ValidationError(error_message)


def ngo_id_number_validator(value):
    cif = "".join([char for char in value.upper() if char.isalnum()])

    if value.startswith("RO"):
        cif = value[2:]

    if not cif.isdigit():
        raise ValidationError(_("The ID number must contain only digits"))

    if 2 > len(cif) or len(cif) > 10:
        raise ValidationError(_("The ID number must be between 2 and 10 digits long"))

    control_key: str = "753217532"

    reversed_key: List[int] = [int(digit) for digit in control_key[::-1]]
    reversed_cif: List[int] = [int(digit) for digit in cif[::-1]]

    cif_control_digit: int = reversed_cif.pop(0)

    cif_key_pairs: Tuple[Tuple[int, int], ...] = tuple(
        cif_digit * key_digit for cif_digit, key_digit in zip(reversed_cif, reversed_key)
    )
    control_result: int = sum(cif_key_pairs) * 10 % 11

    if control_result == cif_control_digit:
        return
    elif control_result == 10 and cif_control_digit == 0:
        return

    raise ValidationError(_("The ID number is not valid"))


class NgoActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Ngo(models.Model):
    slug = models.SlugField(
        verbose_name=_("slug"),
        blank=False,
        null=False,
        max_length=150,
        db_index=True,
        unique=True,
        validators=[ngo_slug_validator],
    )

    name = models.CharField(verbose_name=_("Name"), blank=False, null=False, max_length=200, db_index=True)
    description = models.TextField(verbose_name=_("description"))

    # originally: logo
    logo_url = models.URLField(verbose_name=_("logo url"), blank=True, null=False, default="")
    logo = models.ImageField(
        verbose_name=_("logo"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(ngo_directory_path, "logos"),
    )

    image_url = models.URLField(verbose_name=_("image url"), blank=True, null=False, default="")
    image = models.ImageField(
        verbose_name=_("image"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(ngo_directory_path, "images"),
    )

    # originally: account
    bank_account = models.CharField(verbose_name=_("bank account"), max_length=100)

    # originally: cif
    registration_number = models.CharField(
        verbose_name=_("registration number"),
        max_length=100,
        db_index=True,
        blank=False,
        null=False,
        unique=True,
        validators=[ngo_id_number_validator],
    )

    address = models.TextField(verbose_name=_("address"), blank=True, null=False, default="")
    county = models.CharField(
        verbose_name=_("county"),
        blank=True,
        null=False,
        default="",
        max_length=100,
        db_index=True,
    )
    active_region = models.CharField(
        verbose_name=_("active region"),
        blank=True,
        null=False,
        default="",
        max_length=100,
        db_index=True,
    )

    # originally: tel
    phone = models.CharField(verbose_name=_("telephone"), blank=True, null=False, default="", max_length=30)

    email = models.EmailField(verbose_name=_("email"), blank=True, null=False, default="", db_index=True)
    website = models.URLField(verbose_name=_("website"), blank=True, null=False, default="")
    # TODO: this seems unused
    other_emails = models.TextField(verbose_name=_("other emails"), blank=True, null=False, default="")

    # originally: verified
    is_verified = models.BooleanField(verbose_name=_("is verified"), db_index=True, default=False)

    # originally: special_status
    # if the ngo has a special status (e.g. social ngo) they are entitled to 3.5% donation, not 2%
    has_special_status = models.BooleanField(verbose_name=_("has special status"), db_index=True, default=False)

    # originally: accepts_forms
    # if the ngo accepts to receive donation forms through email
    is_accepting_forms = models.BooleanField(verbose_name=_("is accepting forms"), db_index=True, default=False)

    # originally: active
    is_active = models.BooleanField(verbose_name=_("is active"), db_index=True, default=True)

    # url to the form that contains only the ngo's details
    form_url = models.URLField(
        verbose_name=_("form url"),
        default="",
        blank=True,
        null=False,
        max_length=255,
    )
    prefilled_form = models.FileField(
        verbose_name=_("form with prefilled ngo data"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(year_ngo_directory_path, "ngo-forms"),
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=timezone.now)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=timezone.now)

    objects = models.Manager()
    active = NgoActiveManager()

    def save(self, *args, **kwargs):
        is_new = self.id is None
        self.slug = self.slug.lower()

        super().save(*args, **kwargs)

        if is_new and settings.ENABLE_CACHE:
            cache.delete(ALL_NGOS_CACHE_KEY)

    class Meta:
        verbose_name = _("NGO")
        verbose_name_plural = _("NGOs")

        constraints = [
            models.UniqueConstraint(Lower("slug"), name="slug__unique"),
        ]

    def __str__(self):
        return f"{self.name}"

    def get_full_form_url(self):
        if self.slug:
            return f"redirectioneaza.ro/{self.slug}"
        else:
            return ""

    @staticmethod
    def delete_prefilled_form(ngo_id):
        try:
            ngo = Ngo.objects.get(id=ngo_id)
        except Ngo.DoesNotExist:
            logging.info("NGO id %d does not exist for prefilled form deletion", ngo_id)
            return

        changed = False

        if ngo.form_url:
            ngo.form_url = ""
            changed = True

        if ngo.prefilled_form:
            ngo.prefilled_form.delete(save=False)
            changed = True

        if changed:
            ngo.save()
            logging.info("Prefilled form deleted for NGO id %d", ngo_id)


class DonorSignedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(has_signed=True)


class DonorCurrentYearManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(date_created__year=timezone.now().year)


class DonorCurrentYearSignedManager(DonorSignedManager):
    def get_queryset(self):
        return super().get_queryset().filter(date_created__year=timezone.now().year)


class Donor(models.Model):
    INCOME_CHOICES = (
        ("wage", _("wage")),
        ("pension", _("pension")),
    )

    ngo = models.ForeignKey(Ngo, verbose_name=_("NGO"), on_delete=models.SET_NULL, db_index=True, null=True)

    # TODO: first name and last name have been swapped
    # https://github.com/code4romania/redirectioneaza/issues/269
    first_name = models.CharField(verbose_name=_("last name"), blank=True, null=False, default="", max_length=100)
    last_name = models.CharField(verbose_name=_("first name"), blank=True, null=False, default="", max_length=100)
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
    phone = models.CharField(verbose_name=_("telephone"), blank=True, null=False, default="", max_length=30)
    email = models.EmailField(verbose_name=_("email"), blank=False, null=False, db_index=True)

    # originally: "anonymous"
    is_anonymous = models.BooleanField(
        verbose_name=_("anonymous"),
        db_index=True,
        default=True,
        help_text=_("If the user would like the ngo to see the donation"),
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

    pdf_url = models.URLField(verbose_name=_("PDF URL"), blank=True, null=False, default="", max_length=255)
    filename = models.CharField(verbose_name=_("filename"), blank=True, null=False, default="", max_length=100)
    has_signed = models.BooleanField(verbose_name=_("has signed"), db_index=True, default=False)

    pdf_file = models.FileField(
        verbose_name=_("PDF file"),
        blank=True,
        null=False,
        upload_to=partial(year_ngo_donor_directory_path, "donation-forms"),
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=timezone.now)

    objects = models.Manager()
    signed = DonorSignedManager()
    current_year = DonorCurrentYearManager()
    current_year_signed = DonorCurrentYearSignedManager()

    class Meta:
        verbose_name = _("donor")
        verbose_name_plural = _("donors")

    def __str__(self):
        return f"{self.ngo} {self.date_created} {self.email}"

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
