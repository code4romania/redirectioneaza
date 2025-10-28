from django.db import models
from django.utils.translation import gettext_lazy as _

from donations.models.common import AsyncJob
from users.models import User


class Job(AsyncJob):
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

    number_of_donations = models.IntegerField(verbose_name=_("donations count"), default=-1)
    zip = models.FileField(verbose_name=_("ZIP"), upload_to="donation-zips/%Y/%m/%d/", blank=True, null=True)

    def __str__(self):
        return f"{self.cause} {self.status}"

    class Meta:
        verbose_name = _("job")
        verbose_name_plural = _("jobs")

        ordering = ["-date_created"]
        get_latest_by = "date_created"
