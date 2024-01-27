from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .main import Ngo
from users.models import User


class JobStatusChoices(models.TextChoices):
    NEW = "new", _("New")
    ERROR = "error", _("Error")
    DONE = "done", _("Done")


class Job(models.Model):
    """Keep track for download jobs"""

    ngo = models.ForeignKey(Ngo, verbose_name=_("NGO"), on_delete=models.CASCADE, db_index=True)
    owner = models.ForeignKey(User, verbose_name=_("owner"), on_delete=models.CASCADE, db_index=True)
    status = models.CharField(
        verbose_name=_("status"),
        blank=False,
        null=False,
        default=JobStatusChoices.NEW,
        choices=JobStatusChoices.choices,
        max_length=5,
        db_index=True,
    )
    url = models.URLField(verbose_name=_("URL"), blank=True, null=False, default="", max_length=255)
    date_created = models.DateTimeField(verbose_name=_("date created"), db_index=True, auto_now_add=timezone.now)

    def __str__(self):
        return f"{self.owner} {self.ngo} {self.status}"
