import logging
import re
from functools import partial
from typing import List, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.common.models_hashing import hash_id_secret

ALL_NGOS_CACHE_KEY = "ALL_NGOS"
ALL_NGO_IDS_CACHE_KEY = "ALL_NGO_IDS"
FRONTPAGE_NGOS_KEY = "FRONTPAGE_NGOS"

REGISTRATION_NUMBER_REGEX = r"^([A-Z]{2}|)\d{2,10}$"
REGISTRATION_NUMBER_REGEX_SANS_VAT = r"^\d{2,10}$"
REGISTRATION_NUMBER_REGEX_WITH_VAT = r"^[A-Z]{2}\d{2,10}$"

logger = logging.getLogger(__name__)


def select_public_storage():
    return storages["public"]


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


def ngo_slug_validator(value):
    valid_slug_sample: str = "organizatia-de-exemplu"
    error_message = _("%(value)s is not a valid identifier. The identifier must look like %(sample)s") % {
        "value": value,
        "sample": valid_slug_sample,
    }

    if not value.islower():
        raise ValidationError(error_message)

    if not re.match(r"^[a-z0-9-]+$", value):
        raise ValidationError(error_message)


def ngo_id_number_validator(value):
    reg_num: str = "".join([char for char in value.upper() if char.isalnum()])

    if reg_num == len(reg_num) * "0":
        raise ValidationError(_("The ID number cannot be all zeros"))

    if not re.match(REGISTRATION_NUMBER_REGEX, reg_num):
        raise ValidationError(_("The ID number format is not valid"))

    if re.match(REGISTRATION_NUMBER_REGEX_WITH_VAT, reg_num):
        reg_num = value[2:]

    if not reg_num.isdigit():
        raise ValidationError(_("The ID number must contain only digits"))

    if 2 > len(reg_num) or len(reg_num) > 10:
        raise ValidationError(_("The ID number must be between 2 and 10 digits long"))

    if not settings.ENABLE_FULL_CUI_VALIDATION:
        return

    control_key: str = "753217532"

    reversed_key: List[int] = [int(digit) for digit in control_key[::-1]]
    reversed_cif: List[int] = [int(digit) for digit in reg_num[::-1]]

    cif_control_digit: int = reversed_cif.pop(0)

    cif_key_pairs: Tuple[int, ...] = tuple(
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
        return (
            super()
            .get_queryset()
            .filter(
                is_active=True,
            )
            .exclude(
                Q(name__isnull=True)
                | Q(name__exact="")
                | Q(slug__isnull=True)
                | Q(slug__exact="")
                | Q(bank_account__isnull=True)
                | Q(bank_account__exact="")
                | Q(registration_number__isnull=True)
                | Q(registration_number__exact=""),
            )
        )


class NgoHubManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, ngohub_org_id__isnull=False)


class NgoWithFormsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, is_accepting_forms=True)


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

    # NGO Hub details
    ngohub_org_id = models.IntegerField(
        verbose_name=_("NGO Hub organization ID"),
        blank=True,
        null=True,
        db_index=True,
        unique=True,
    )
    ngohub_last_update_started = models.DateTimeField(_("Last NGO Hub update"), null=True, blank=True, editable=False)
    ngohub_last_update_ended = models.DateTimeField(_("Last NGO Hub update"), null=True, blank=True, editable=False)

    # originally: logo
    logo = models.ImageField(
        verbose_name=_("logo"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(ngo_directory_path, "logos"),
    )

    # originally: account
    bank_account = models.CharField(verbose_name=_("bank account"), max_length=100)

    # originally: cif
    # TODO: the number's length should be between 2 and 10 (or 8)
    registration_number = models.CharField(
        verbose_name=_("registration number"),
        max_length=100,
        db_index=True,
        blank=False,
        null=False,
        unique=True,
        validators=[ngo_id_number_validator],
    )
    vat_id = models.CharField(
        verbose_name=_("VAT ID"),
        max_length=2,
        blank=True,
        null=False,
        default="",
        db_index=True,
    )
    registration_number_valid = models.BooleanField(
        verbose_name=_("registration validation failed"),
        db_index=True,
        null=True,
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

    # originally: verified
    is_verified = models.BooleanField(verbose_name=_("is verified"), db_index=True, default=False)

    # originally: special_status
    # if the ngo has a special status (e.g. social ngo) they are entitled to 3.5% donation, not 2%
    is_social_service_viable = models.BooleanField(verbose_name=_("has special status"), db_index=True, default=False)

    # originally: accepts_forms
    # if the ngo accepts to receive donation forms through email
    is_accepting_forms = models.BooleanField(verbose_name=_("is accepting forms"), db_index=True, default=True)

    # originally: active — the user cannot modify this property, it is set by the admin/by the NGO Hub settings
    is_active = models.BooleanField(verbose_name=_("is active"), db_index=True, default=True)

    # url to the form that contains only the ngo's details
    prefilled_form = models.FileField(
        verbose_name=_("form with prefilled ngo data"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(year_ngo_directory_path, "ngo-forms"),
    )

    filename_cache = models.JSONField(_("Filename cache"), editable=False, default=dict, blank=False, null=False)

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=True)

    objects = models.Manager()
    active = NgoActiveManager()
    ngo_hub = NgoHubManager()
    with_forms = NgoWithFormsManager()

    def save(self, *args, **kwargs):
        is_new = self.id is None
        self.slug = self.slug.lower()

        if self.registration_number:
            uppercase_registration_number = self.registration_number
            if re.match(REGISTRATION_NUMBER_REGEX_WITH_VAT, uppercase_registration_number):
                self.vat_id = uppercase_registration_number[:2]
                self.registration_number = uppercase_registration_number[2:]

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

    def activate(self, commit: bool = True):
        if self.is_active:
            return

        self.is_active = True

        if commit:
            self.save()

    def deactivate(self, commit: bool = True):
        if not self.is_active:
            return

        self.is_active = False

        if commit:
            self.save()

    @staticmethod
    def delete_prefilled_form(ngo_id):
        try:
            ngo = Ngo.objects.get(id=ngo_id)
        except Ngo.DoesNotExist:
            logging.info("NGO id %d does not exist for prefilled form deletion", ngo_id)
            return

        changed = False

        if ngo.prefilled_form:
            ngo.prefilled_form.delete(save=False)
            changed = True

        if changed:
            ngo.save()
            logging.info("Prefilled form deleted for NGO id %d", ngo_id)
