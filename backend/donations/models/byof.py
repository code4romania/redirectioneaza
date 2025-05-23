from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Ngo


@deconstructible
class MaxFileSizeValidator:
    """
    Validator which checks that file size is less or equal to the specified size limit
    """

    def __init__(self, max_size=1024):
        self.max_size = max_size

    def __call__(self, value):
        if not value and not hasattr(value, "size"):
            return
        if value.size > self.max_size:
            raise ValidationError(_("File size must not exceed {mb} MB").format(mb=self.max_size / settings.MEBIBYTE))


class OwnFormsStatusChoices(models.TextChoices):
    NEW = "new", _("newly uploaded")
    VALIDATING = "vali", _("validating uploaded data")
    PROCESSING = "proc", _("processing")
    FAILED = "fail", _("failed")
    SUCCESS = "succ", _("success")


class NewOwnFormsUploadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=OwnFormsStatusChoices.NEW)


class DoneOwnFormsUploadManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                status__in=(
                    OwnFormsStatusChoices.FAILED,
                    OwnFormsStatusChoices.SUCCESS,
                )
            )
        )


class OwnFormsUpload(models.Model):
    ngo = models.ForeignKey(Ngo, on_delete=models.CASCADE, related_name="own_forms_uploads")
    bank_account = models.CharField(verbose_name=_("IBAN"), max_length=24, blank=False, null=False)
    uploaded_data = models.FileField(
        verbose_name=_("uploaded data"),
        upload_to="own-forms/%Y/%m/%d/",
        blank=False,
        null=False,
        validators=(
            FileExtensionValidator(allowed_extensions=("csv",)),
            MaxFileSizeValidator(2 * settings.MEBIBYTE),
        ),
    )
    items_count = models.PositiveBigIntegerField(verbose_name=_("form count"), blank=False, null=False, default=0)
    result_data = models.FileField(
        verbose_name=_("result data"), upload_to="own-forms/%Y/%m/%d/", blank=True, null=True
    )
    result_text = models.TextField(verbose_name=_("result text"), blank=True, null=True, default="")
    status = models.CharField(
        verbose_name=_("status"),
        blank=False,
        null=False,
        default=OwnFormsStatusChoices.NEW,
        max_length=4,
        db_index=True,
        choices=OwnFormsStatusChoices.choices,
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=True)

    objects = models.Manager()
    new_uploads = NewOwnFormsUploadManager()
    done = DoneOwnFormsUploadManager()

    class Meta:
        verbose_name = _("bring your own forms upload")
        verbose_name_plural = _("bring your own forms uploads")

    def __str__(self):
        return self.bank_account

    @property
    def is_successful(self):
        return self.status == OwnFormsStatusChoices.SUCCESS

    @property
    def is_failed(self):
        return self.status == OwnFormsStatusChoices.FAILED

    @property
    def is_in_progress(self):
        return self.status != OwnFormsStatusChoices.FAILED and self.status != OwnFormsStatusChoices.SUCCESS
