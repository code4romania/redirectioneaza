from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class JobError(Exception):
    pass


class JobDownloadError(JobError):
    pass


class JobStatusChoices(models.TextChoices):
    NEW = "new", _("New")
    ERROR = "error", _("Error")
    DONE = "done", _("Done")


class AsyncJob(models.Model):
    status = models.CharField(
        verbose_name=_("status"),
        blank=False,
        null=False,
        default=JobStatusChoices.NEW,
        choices=JobStatusChoices.choices,
        max_length=5,
        db_index=True,
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=True)
    date_finished = models.DateTimeField(verbose_name=_("date finished"), db_index=True, blank=True, null=True)

    objects = models.Manager()

    def save(self, *args, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.status == JobStatusChoices.DONE and not self.date_finished:
            self.date_finished = timezone.now()

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True


class CommonFilenameCacheModel(models.Model):
    """
    A model that has a cache for filenames.
    """

    filename_cache = models.JSONField(_("Filename cache"), editable=False, default=dict, blank=False, null=False)

    class Meta:
        abstract = True
