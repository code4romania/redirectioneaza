import logging
import re
from functools import partial
from typing import List

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.db.models.query_utils import DeferredAttribute
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.common.models_hashing import hash_id_secret
from donations.common.validation.clean_slug import clean_slug
from donations.common.validation.registration_number import REGISTRATION_NUMBER_REGEX_WITH_VAT, ngo_id_number_validator

ALL_NGOS_CACHE_KEY = "ALL_NGOS"
ALL_NGO_IDS_CACHE_KEY = "ALL_NGO_IDS"
FRONTPAGE_NGOS_KEY = "FRONTPAGE_NGOS"
FRONTPAGE_STATS_KEY = "FRONTPAGE_NGOS_STATS"

logger = logging.getLogger(__name__)


def select_public_storage():
    return storages["public"]


def ngo_directory_path(subdir: str, instance: "Ngo", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/ngo-<id>-<hash>/<filename>
    """
    ngo_pk = instance.pk
    ngo_hash = hash_id_secret("ngo", ngo_pk)

    return f"{subdir}/ngo-{ngo_pk}-{ngo_hash}/{filename}"


def ngo_form_directory_path(subdir: str, instance: "Cause", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/ngo-<id>-<hash>/<filename>
    """
    ngo_pk = instance.ngo.pk
    form_pk = instance.pk
    form_hash = hash_id_secret("ngo-form", form_pk)

    return f"{subdir}/ngo-{ngo_pk}/form-{form_pk}-{form_hash}/{filename}"


def year_ngo_directory_path(subdir: str, instance: "Ngo", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/ngo-<id>-<hash>/<filename>
    """
    timestamp = timezone.now()

    year = timestamp.date().year

    ngo_pk = instance.pk
    ngo_hash = hash_id_secret("ngo", ngo_pk)

    return f"{subdir}/{year}/ngo-{ngo_pk}-{ngo_hash}/{filename}"


def year_cause_directory_path(subdir: str, instance: "Cause", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/ngo-<id>-<hash>/<filename>
    """
    timestamp = timezone.now()

    year = timestamp.date().year

    ngo_pk = instance.ngo.pk
    ngo_hash = hash_id_secret("ngo", ngo_pk)

    cause_pk = instance.pk
    cause_hash = hash_id_secret("cause", cause_pk)

    return f"{subdir}/{year}/ngo-{ngo_pk}-{ngo_hash}/c-{cause_pk}-{cause_hash}/{filename}"


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


class CauseActiveManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(ngo__is_active=True)
            .exclude(
                Q(name__isnull=True)
                | Q(name__exact="")
                | Q(slug__isnull=True)
                | Q(slug__exact="")
                | Q(bank_account__isnull=True)
                | Q(bank_account__exact="")
                | Q(ngo__registration_number__isnull=True)
                | Q(ngo__registration_number__exact=""),
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
    # XXX: [MULTI-FORM] Move to Cause
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
    # XXX: [MULTI-FORM] Should we move this to Cause ???
    logo = models.ImageField(
        verbose_name=_("logo"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(ngo_directory_path, "logos"),
    )

    # XXX: [MULTI-FORM] Move to Cause
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
    locality = models.CharField(
        verbose_name=_("locality"),
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
    active_region = models.CharField(
        verbose_name=_("active region"),
        blank=True,
        null=False,
        default="",
        max_length=100,
        db_index=True,
    )

    email = models.EmailField(verbose_name=_("email"), blank=True, null=False, default="", db_index=True)
    phone = models.CharField(verbose_name=_("telephone"), blank=True, null=False, default="", max_length=30)

    display_email = models.BooleanField(verbose_name=_("display email"), db_index=True, default=False)
    display_phone = models.BooleanField(verbose_name=_("display phone"), db_index=True, default=False)

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
        if not self.slug:
            self.slug = clean_slug(self.name)

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

    @property
    def mandatory_fields(self):

        # noinspection PyTypeChecker
        field_names: List[DeferredAttribute] = [
            Ngo.name,
            Ngo.slug,
            Ngo.description,
            Ngo.registration_number,
            Ngo.bank_account,
        ]

        return [field.field for field in field_names]

    def missing_mandatory_fields(self):
        return [field for field in self.mandatory_fields if not getattr(self, field.name)]

    @property
    def mandatory_fields_names(self):
        return [field.verbose_name for field in self.mandatory_fields]

    @property
    def mandatory_fields_names_lower(self):
        return [field.lower() for field in self.mandatory_fields_names]

    @property
    def mandatory_fields_names_capitalize(self):
        return [field.capitalize() for field in self.mandatory_fields_names]

    @property
    def missing_mandatory_fields_names(self):
        return [field.verbose_name for field in self.missing_mandatory_fields()]

    @property
    def missing_mandatory_fields_names_lower(self):
        return [field.lower() for field in self.missing_mandatory_fields_names]

    @property
    def missing_mandatory_fields_names_capitalize(self):
        return [field.capitalize() for field in self.missing_mandatory_fields_names]

    def mandatory_fields_values(self):
        return [getattr(self, field.name) for field in self.mandatory_fields]

    def can_receive_forms(self):
        if not self.is_active:
            return False

        if not all(self.mandatory_fields_values()):
            return False

        return True

    @property
    def full_registration_number(self):
        return f"{self.vat_id}{self.registration_number}" if self.vat_id else self.registration_number

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


class Cause(models.Model):
    ngo = models.ForeignKey(Ngo, on_delete=models.CASCADE, related_name="causes")

    allow_online_collection = models.BooleanField(verbose_name=_("allow online collection"), default=False)

    display_image = models.ImageField(
        verbose_name=_("logo"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(ngo_directory_path, "logos"),
    )

    slug = models.SlugField(
        verbose_name=_("slug"),
        blank=False,
        null=False,
        max_length=150,
        db_index=True,
        unique=True,
        validators=[ngo_slug_validator],
    )

    name = models.CharField(verbose_name=_("name"), blank=False, null=False, max_length=200, db_index=True)
    description = models.TextField(verbose_name=_("description"))

    bank_account = models.CharField(verbose_name=_("bank account"), max_length=100)

    prefilled_form = models.FileField(
        verbose_name=_("form with prefilled cause"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(year_cause_directory_path, "causes"),
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=True)

    objects = models.Manager()
    active = CauseActiveManager()

    class Meta:
        verbose_name = _("Cause")
        verbose_name_plural = _("Causes")

    def __str__(self):
        return f"{self.ngo.name} - {self.name}"
