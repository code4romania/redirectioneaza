from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


class Stat(models.Model):
    name = models.CharField(_("name"), max_length=100, db_index=True)

    date = models.DateField(_("date"), null=True, blank=True, db_index=True)

    value = models.DecimalField(_("value"), max_digits=11, decimal_places=2, null=True, blank=True)

    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    expires_at = models.DateTimeField(_("expires at"), null=True, blank=True)

    def __str__(self):
        return f"{self.name}: {self.value}"

    class Meta:
        verbose_name = _("statistic")
        verbose_name_plural = _("statistics")

        ordering = ["-date", "name"]

        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "date",
                name="unique_stat_name_date",
            ),
        ]
