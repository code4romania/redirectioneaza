from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task


class ImportModelTypeChoices(models.TextChoices):
    USER = "users.User", "User"
    NGO = "donations.Ngo", "Ngo"
    DONOR = "donations.Donor", "Donor"
    PARTNER = "partners.Partner", "Partner"


class ImportStatusChoices(models.TextChoices):
    PENDING = "pending", _("Pending")
    PROCESSING = "working", _("Processing")
    DONE = "done", _("Done")
    ERROR = "error", _("Error")


class ImportJob(models.Model):
    import_type = models.CharField(_("Import type"), max_length=32, choices=ImportModelTypeChoices.choices)
    status = models.CharField(
        _("Status"), max_length=10, choices=ImportStatusChoices.choices, default=ImportStatusChoices.PENDING
    )

    has_header = models.BooleanField(_("Has header"), blank=False, null=False, default=True)
    csv_file = models.FileField(_("File"), upload_to="imports/%Y/%m/%d/")

    uploaded_at = models.DateTimeField(_("Uploaded at"), auto_now_add=timezone.now)

    def process_import(self):
        import_id = self.id

        async_task("importer.tasks.processor.process_import_task", import_id)

    class Meta:
        verbose_name = _("Import")
        verbose_name_plural = _("Imports")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        if self.status == ImportStatusChoices.PENDING:
            self.process_import()
