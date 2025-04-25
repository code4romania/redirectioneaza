from django.db import models
from django.utils.translation import gettext_lazy as _

from donations.models.common import AsyncJob


class RedirectionsDownloadJob(AsyncJob):
    ngo = models.ForeignKey(
        "Ngo",
        verbose_name=_("NGO"),
        on_delete=models.CASCADE,
        db_index=True,
        related_name="download_jobs",
    )

    queryset = models.JSONField(verbose_name=_("queryset"), blank=False, null=False)

    output_rows = models.IntegerField(verbose_name=_("rows count"), default=-1)
    output_file = models.FileField(
        verbose_name=_("output file"),
        upload_to="donation-downloads/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("download job")
        verbose_name_plural = _("download jobs")

        ordering = ["-date_created"]
        get_latest_by = "date_created"
