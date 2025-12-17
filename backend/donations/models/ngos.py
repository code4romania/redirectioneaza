import logging
import re
from functools import partial
from typing import Any

from auditlog.registry import auditlog
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
from donations.models.common import CommonFilenameCacheModel
from donations.models.donors import Donor
from utils.text.registration_number import (
    REGISTRATION_NUMBER_REGEX_WITH_VAT,
    ngo_id_number_validator,
)

ALL_NGOS_CACHE_KEY = "ALL_NGOS"
ALL_NGO_IDS_CACHE_KEY = "ALL_NGO_IDS"
FRONTPAGE_NGOS_KEY = "FRONTPAGE_NGOS"
FRONTPAGE_STATS_KEY = "FRONTPAGE_NGOS_STATS"
NGO_CAUSES_QUERY_CACHE_KEY = "NGO_CAUSES_{ngo.pk}"

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


def cause_directory_path(subdir: str, instance: "Cause", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/ngo-<ngo.id>/c-<cause.id>-<cause.hash>/<filename>
    """
    ngo_pk = instance.ngo.pk

    cause_pk = instance.pk
    cause_hash = hash_id_secret("cause", cause_pk)

    return f"{subdir}/ngo-{ngo_pk}/c-{cause_pk}-{cause_hash}/{filename}"


def year_ngo_directory_path(subdir: str, instance: "Ngo", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/ngo-<ngo.id>-<ngo.hash>/<filename>
    """
    timestamp = timezone.now()

    year = timestamp.date().year

    ngo_pk = instance.pk
    ngo_hash = hash_id_secret("ngo", ngo_pk)

    return f"{subdir}/{year}/ngo-{ngo_pk}-{ngo_hash}/{filename}"


def year_cause_directory_path(subdir: str, instance: "Cause", filename: str) -> str:
    """
    The file will be uploaded to MEDIA_ROOT/<subdir>/<year>/c-<cause.id>-<cause.hash>/<filename>
    """
    timestamp = timezone.now()

    year = timestamp.date().year

    cause_pk = instance.pk
    cause_hash = hash_id_secret("cause", cause_pk)

    return f"{subdir}/{year}/c-{cause_pk}-{cause_hash}/{filename}"


def ngo_slug_validator(value):
    valid_slug_sample: str = "organizatia-de-exemplu"
    error_message = _("'%(value)s' is not a valid identifier. The identifier must look like %(sample)s") % {
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
                | Q(registration_number__isnull=True)
                | Q(registration_number__exact=""),
            )
            # TODO: also exclude NGOs which do not have at least one Cause with a bank account or slug
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


class CausePublicFormManager(CauseActiveManager):
    def get_queryset(self):
        return super().get_queryset().filter(visibility=CauseVisibilityChoices.PUBLIC)


class CauseNonPrivateFormManager(CauseActiveManager):
    def get_queryset(self):
        return super().get_queryset().exclude(visibility=CauseVisibilityChoices.PRIVATE)


class CauseMainManager(CauseActiveManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_main=True)


class CauseOtherManager(CauseActiveManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_main=False)


class NgoHubManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, ngohub_org_id__isnull=False)


class NgoWithFormsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, has_online_tax_account=True)


class NgoWithFormsThisYearManager(models.Manager):
    def get_queryset(self):
        donations_ngos = Donor.available.filter(date_created__year=timezone.now().year).values("ngo_id").distinct()
        return super().get_queryset().filter(pk__in=donations_ngos)


class Ngo(CommonFilenameCacheModel):
    name = models.CharField(verbose_name=_("Legal name"), blank=False, null=False, max_length=200, db_index=True)

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

    active_region = models.TextField(verbose_name=_("active region"), blank=True, null=False, default="")

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

    has_online_tax_account = models.BooleanField(verbose_name=_("has online tax account"), db_index=True, default=False)

    # originally: active — the user cannot modify this property, it is set by the admin/by the NGO Hub settings
    is_active = models.BooleanField(verbose_name=_("is active"), db_index=True, default=True)

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=True)

    objects = models.Manager()
    active = NgoActiveManager()
    ngo_hub = NgoHubManager()
    with_forms_this_year = NgoWithFormsThisYearManager()

    class Meta:
        verbose_name = _("NGO")
        verbose_name_plural = _("NGOs")

        constraints = [
            models.UniqueConstraint(Lower("registration_number"), name="registration_number__unique"),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        is_new = self.id is None

        if self.registration_number:
            uppercase_registration_number = self.registration_number
            if re.match(REGISTRATION_NUMBER_REGEX_WITH_VAT, uppercase_registration_number):
                self.vat_id = uppercase_registration_number[:2]
                self.registration_number = uppercase_registration_number[2:]

        if not is_new and not self.has_online_tax_account:
            old_self: Ngo = Ngo.objects.get(pk=self.pk)
            if old_self.has_online_tax_account != self.has_online_tax_account:
                self.causes.update(allow_online_collection=False, notifications_email="")

        super().save(*args, **kwargs)

        if is_new and settings.ENABLE_CACHE:
            cache.delete(ALL_NGOS_CACHE_KEY)

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
    def main_cause(self) -> "Cause | None":
        if not self.pk:
            return None

        return self.causes.filter(is_main=True).first()

    @property
    def slug(self):
        if main_cause := self.main_cause:
            return main_cause.slug

        return None

    @property
    def description(self):
        if main_cause := self.main_cause:
            return main_cause.description

        return None

    @property
    def logo(self):
        if main_cause := self.main_cause:
            return main_cause.display_image

        return None

    @property
    def bank_account(self):
        if main_cause := self.main_cause:
            return main_cause.bank_account

        return None

    @property
    def prefilled_form(self):
        if main_cause := self.main_cause:
            return main_cause.prefilled_form

        return None

    @property
    def has_ngo_hub(self):
        return bool(self.ngohub_org_id)

    @classmethod
    def mandatory_fields(cls):
        # noinspection PyTypeChecker
        field_names: list[DeferredAttribute] = [
            Ngo.name,
            Ngo.registration_number,
        ]

        return [field.field for field in field_names]

    def missing_mandatory_fields(self):
        return [field for field in self.mandatory_fields() if not getattr(self, field.name)]

    @classmethod
    def mandatory_fields_names(cls):
        return [field.verbose_name for field in cls.mandatory_fields()]

    @classmethod
    def mandatory_fields_names_capitalized(cls):
        return [field.capitalize() for field in cls.mandatory_fields_names()]

    @property
    def missing_mandatory_fields_names(self):
        return [field.verbose_name for field in self.missing_mandatory_fields()]

    @property
    def missing_mandatory_fields_names_capitalize(self):
        return [field.capitalize() for field in self.missing_mandatory_fields_names]

    @property
    def can_create_causes(self):
        """
        An NGO can create causes if they are active and have all the mandatory fields filled
        """
        if not self.is_active:
            return False

        if any(self.missing_mandatory_fields()):
            return False

        return True

    @property
    def can_receive_redirections(self):
        """
        An NGO can receive donations if it is active and has all the mandatory fields filled
        """
        if not self.can_create_causes:
            return False

        main_cause: Cause | None = self.main_cause
        if not main_cause:
            return False

        if not main_cause.can_receive_redirections:
            return False

        return True

    @property
    def has_spv_option(self) -> str:
        return "yes" if self.has_online_tax_account else "no"

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

        for cause in ngo.causes.all():
            cause.delete_prefilled_form()


class CauseVisibilityChoices(models.TextChoices):
    PUBLIC = "pub", _("public")
    UNLISTED = "unl", _("unlisted")
    PRIVATE = "pri", _("private")

    @staticmethod
    def as_dict():
        result = []
        for choice in CauseVisibilityChoices.choices:
            result.append({"title": choice[1], "value": choice[0]})
        return result

    @staticmethod
    def as_str():
        return str(CauseVisibilityChoices.as_dict())

    @staticmethod
    def as_str_pretty():
        choices = CauseVisibilityChoices.as_dict()
        return [{**choice, "title": choice["title"].capitalize()} for choice in choices]


class Cause(CommonFilenameCacheModel):
    ngo = models.ForeignKey(Ngo, on_delete=models.CASCADE, related_name="causes")

    is_main = models.BooleanField(verbose_name=_("is main cause"), db_index=True, default=False)
    allow_online_collection = models.BooleanField(verbose_name=_("allow online collection"), default=False)

    visibility = models.CharField(
        verbose_name=_("form visibility"),
        max_length=3,
        default=CauseVisibilityChoices.PUBLIC,
        blank=False,
        null=False,
        db_index=True,
        choices=CauseVisibilityChoices.choices,
    )

    display_image = models.ImageField(
        verbose_name=_("logo"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(cause_directory_path, "logos"),
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

    notifications_email = models.EmailField(verbose_name=_("notifications email"), blank=True, null=False, default="")

    prefilled_form = models.FileField(
        verbose_name=_("form with prefilled cause"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(year_cause_directory_path, "ngo-forms"),
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=True)

    objects = models.Manager()
    active = CauseActiveManager()
    main = CauseMainManager()
    other = CauseOtherManager()
    public_active = CausePublicFormManager()
    nonprivate_active = CauseNonPrivateFormManager()

    class Meta:
        verbose_name = _("Cause")
        verbose_name_plural = _("Causes")
        constraints = [
            models.UniqueConstraint(fields=["ngo", "bank_account"], name="ngo_bank_account_unique"),
            models.UniqueConstraint(fields=["ngo"], condition=Q(is_main=True), name="ngo_main_cause_unique"),
        ]

    def __str__(self):
        return f"{self.ngo.name} - {self.name}"

    @property
    def allow_online_notifications(self):
        return bool(self.notifications_email)

    @classmethod
    def mandatory_fields(cls):
        # noinspection PyTypeChecker
        field_names: list[DeferredAttribute] = [
            Cause.name,
            Cause.slug,
            Cause.description,
            Cause.bank_account,
        ]

        return [field.field for field in field_names]

    @classmethod
    def mandatory_fields_names(cls):
        return [field.verbose_name for field in cls.mandatory_fields()]

    @classmethod
    def mandatory_fields_names_capitalized(cls):
        return [field.capitalize() for field in cls.mandatory_fields_names()]

    @property
    def is_public(self):
        return self.visibility == CauseVisibilityChoices.PUBLIC

    @property
    def is_private(self):
        return self.visibility == CauseVisibilityChoices.PRIVATE

    @property
    def missing_mandatory_fields(self):
        return [field for field in Cause.mandatory_fields() if not getattr(self, field.name)]

    @property
    def missing_mandatory_fields_names(self):
        return [field.verbose_name for field in self.missing_mandatory_fields]

    def missing_mandatory_fields_names_capitalized(self):
        return [field.capitalize() for field in self.missing_mandatory_fields_names]

    @property
    def mandatory_fields_values(self) -> list[Any]:
        return [getattr(self, field.name) for field in Cause.mandatory_fields()]

    @property
    def redirections_count(self):
        return self.donor_set.count()

    @property
    def can_receive_redirections(self):
        """
        A cause can receive donations if all the mandatory fields are filled
        """
        if not all(self.mandatory_fields_values):
            return False

        return True

    def delete_prefilled_form(self):
        if self.prefilled_form:
            self.prefilled_form.delete()


auditlog.register(Ngo)
auditlog.register(Cause)
