from django.db import models
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Ngo


class OwnFormsStatusChoices(models.TextChoices):
    NEW = "new", _("public")
    VALIDATING = "vali", _("validating uploaded data")
    PENDING_PROCESSING = "pend", _("awaiting processing")
    PROCESSING = "proc", _("processing")
    FAILED = "fail", _("failed")
    SUCCESS = "succ", _("success")


class NewOwnFormsUploadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=OwnFormsStatusChoices.NEW)


class PendingOwnFormsUploadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=OwnFormsStatusChoices.PENDING_PROCESSING)


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
    bank_account = models.CharField(verbose_name=_("IBAN"), max_length=24, min_length=24, required=True)
    uploaded_data = models.FileField(
        verbose_name=_("uploaded data"), upload_to="own-forms/%Y/%m/%d/", blank=False, null=False
    )
    result_data = models.FileField(
        verbose_name=_("result data"), upload_to="own-forms/%Y/%m/%d/", blank=True, null=True
    )
    status = models.CharField(
        verbose_name=_("status"),
        blank=False,
        null=False,
        default=OwnFormsStatusChoices.NEW,
        max_length=4,
        db_index=True,
        choices=OwnFormsStatusChoices.choices,
    )

    # TODO: store details about errors in order to display them to the user

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), db_index=True, auto_now=True)

    objects = models.Manager()
    new_uploads = NewOwnFormsUploadManager()
    pending_processing = PendingOwnFormsUploadManager()
    done = DoneOwnFormsUploadManager()

    class Meta:
        verbose_name = _("bring your own forms upload")
        verbose_name_plural = _("bring your own forms uploads")
