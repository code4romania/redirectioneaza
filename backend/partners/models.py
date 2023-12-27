from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from donations.models import Ngo


class Partner(models.Model):
    name = models.CharField(verbose_name=_("name"),max_length=100, blank=True,null=False,db_index=True)
    subdomain = models.CharField(verbose_name=_("subdomain"),max_length=100, blank=False, null=False, unique=True)
    is_active = models.BooleanField(verbose_name=_("is active"), db_index=True, default=True)
    ngos = models.ManyToManyField(verbose_name=_("NGOs"), to=Ngo)

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")
        constraints = [
            models.UniqueConstraint(Lower("subdomain"), name="subdomain_unique"),
        ]

    def __str__(self):
        return f"{self.name}"

