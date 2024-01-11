import hashlib

from functools import partial
from django.conf import settings
from django.core.files.storage import storages
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_cryptography.fields import encrypt


def select_public_storage():
    return storages["public"]


def ngo_directory_path(subdir, instance, filename) -> str:
    ngo_code: str = hashlib.sha1(f"ngo-{instance.pk}-{settings.SECRET_KEY}".encode()).hexdigest()

    # file will be uploaded to MEDIA_ROOT/ngo-<id>-<hash>/<subdir>/<filename>
    return "ngo-{0}-{1}/{2}/{3}".format(instance.pk, ngo_code[:10], subdir, filename)


def year_directory_path(subdir, instance, filename) -> str:
    timestamp = timezone.now()
    return "{0}/{1}/{2}/{3}".format(subdir, timestamp.date().year, instance.pk, filename)


class Ngo(models.Model):
    # DEFAULT_NGO_LOGO = "https://storage.googleapis.com/redirectioneaza/logo_bw.png"

    name = models.CharField(verbose_name=_("Name"), blank=False, null=False, max_length=100, db_index=True)
    description = models.TextField(
        verbose_name=_("description"),
    )

    # originally: logo
    logo_url = models.URLField(verbose_name=_("logo url"), blank=True, null=False, default="")
    logo = models.ImageField(
        verbose_name=_("logo"),
        blank=True,
        null=False,
        storage=select_public_storage,
        upload_to=partial(ngo_directory_path, "logos"),
    )

    # originally: image_url
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

    # TODO: this seems to act as an unique NGO identifier
    # TODO: rename it to "identifier" in a future version
    # url to the ngo's 2% form, that contains only the ngo's details
    form_url = models.SlugField(
        verbose_name=_("form url"), blank=False, max_length=100, unique=True, null=True
    )  # noqa: DJ001

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=timezone.now)

    class Meta:
        verbose_name = _("NGO")
        verbose_name_plural = _("NGOs")
        constraints = [
            models.UniqueConstraint(Lower("form_url"), name="form_url_unique"),
        ]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        # Force the form_url (which acts as an NGO identifier) to lowercase
        if self.form_url:
            self.form_url = self.form_url.lower().strip()
        return super().save(*args, **kwargs)

    def get_full_form_url(self):
        if self.form_url:
            return "https://{}/{}".format(settings.APEX_DOMAIN, self.form_url)
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
        upload_to=partial(year_directory_path, "documents"),
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=timezone.now)

    class Meta:
        verbose_name = _("donor")
        verbose_name_plural = _("donors")

    def __str__(self):
        return f"{self.ngo} {self.date_created} {self.email}"
