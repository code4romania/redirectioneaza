import hashlib
from functools import partial

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_cryptography.fields import encrypt


def select_public_storage():
    return storages["public"]


def hash_id_secret(prefix: str, id: int) -> str:
    return hashlib.sha1(f"{prefix}-{id}-{settings.SECRET_KEY}".encode()).hexdigest()[:10]


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
    valid_slug_sample: str = "asociatia-de-exemplu"
    error_message = _("%(value)s is not a valid identifier. The identifier must look like %(sample)s") % {
        "value": value,
        "sample": valid_slug_sample,
    }

    if not value.islower():
        raise ValidationError(error_message)


def ngo_id_number_validator(value):
    error_message = _("The ID number must be 8 digits long")
    if len(value) != 8:
        raise ValidationError(error_message)


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Ngo(models.Model):
    # DEFAULT_NGO_LOGO = "https://storage.googleapis.com/redirectioneaza/logo_bw.png"

    slug = models.SlugField(
        verbose_name=_("slug"),
        blank=False,
        null=False,
        max_length=100,
        db_index=True,
        unique=True,
        validators=[ngo_slug_validator],
    )

    name = models.CharField(verbose_name=_("Name"), blank=False, null=False, max_length=100, db_index=True)
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
    active = ActiveManager()

    class Meta:
        verbose_name = _("NGO")
        verbose_name_plural = _("NGOs")

        constraints = [
            models.UniqueConstraint(Lower("slug"), name="slug__unique"),
        ]

    def __str__(self):
        return f"{self.name}"

    def get_full_form_url(self):
        if self.prefilled_form:
            return self.prefilled_form.url
        elif self.form_url:
            return self.form_url
        else:
            return ""


class Donor(models.Model):
    INCOME_CHOICES = (
        ("wage", _("wage")),
        ("pension", _("pension")),
    )

    ngo = models.ForeignKey(Ngo, verbose_name=_("NGO"), on_delete=models.CASCADE, db_index=True)

    first_name = models.CharField(verbose_name=_("first name"), blank=True, null=False, default="", max_length=100)
    last_name = models.CharField(verbose_name=_("last name"), blank=True, null=False, default="", max_length=100)
    initial = models.CharField(verbose_name=_("initials"), blank=True, null=False, default="", max_length=5)

    cnp = encrypt(models.CharField(verbose_name=_("CNP"), blank=True, null=False, default="", max_length=13))

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
    address = models.JSONField(verbose_name=_("address"), blank=True, null=False, default=dict)

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

    class Meta:
        verbose_name = _("donor")
        verbose_name_plural = _("donors")

    def __str__(self):
        return f"{self.ngo} {self.date_created} {self.email}"
