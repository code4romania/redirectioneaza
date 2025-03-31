from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from users.models import User


class JobError(Exception):
    pass


class JobDownloadError(JobError):
    pass


class JobStatusChoices(models.TextChoices):
    NEW = "new", _("New")
    ERROR = "error", _("Error")
    DONE = "done", _("Done")


class Job(models.Model):
    """Keep track of download jobs"""

    ngo = models.ForeignKey(
        "Ngo",
        verbose_name=_("NGO"),
        on_delete=models.CASCADE,
        db_index=True,
        related_name="jobs",
    )
    cause = models.ForeignKey(
        "Cause",
        verbose_name=_("cause"),
        on_delete=models.CASCADE,
        db_index=True,
        related_name="jobs",
        null=True,
    )
    owner = models.ForeignKey(
        User,
        verbose_name=_("owner"),
        on_delete=models.CASCADE,
        db_index=True,
        related_name="jobs",
    )
    status = models.CharField(
        verbose_name=_("status"),
        blank=False,
        null=False,
        default=JobStatusChoices.NEW,
        choices=JobStatusChoices.choices,
        max_length=5,
        db_index=True,
    )

    number_of_donations = models.IntegerField(verbose_name=_("donations count"), default=-1)
    zip = models.FileField(verbose_name=_("ZIP"), upload_to="donation-zips/%Y/%m/%d/", blank=True, null=True)

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_finished = models.DateTimeField(verbose_name=_("date finished"), db_index=True, blank=True, null=True)

    def __str__(self):
        return f"{self.cause} {self.status}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.status == JobStatusChoices.DONE and not self.date_finished:
            self.date_finished = timezone.now()

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        verbose_name = _("job")
        verbose_name_plural = _("jobs")

        ordering = ["-date_created"]
        get_latest_by = "date_created"
