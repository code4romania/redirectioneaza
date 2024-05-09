from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from donations.models.main import Ngo
from redirectioneaza.common.validators import url_validator


class DisplayOrderingChoices(models.TextChoices):
    ALPHABETICAL = "ABC", _("Alphabetical")
    NEWEST = "AGE", _("Newest")
    RANDOM = "RND", _("Random")


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Partner(models.Model):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=100,
        blank=True,
        null=False,
        db_index=True,
    )
    subdomain = models.CharField(
        verbose_name=_("subdomain"),
        max_length=100,
        blank=False,
        null=False,
        unique=True,
        validators=[url_validator],
    )
    is_active = models.BooleanField(
        verbose_name=_("is active"),
        db_index=True,
        default=True,
    )

    has_custom_header = models.BooleanField(verbose_name=_("has custom header"), default=False)
    has_custom_note = models.BooleanField(verbose_name=_("has custom note"), default=False)
    display_ordering = models.CharField(
        verbose_name=_("display ordering"),
        max_length=3,
        choices=DisplayOrderingChoices.choices,
        default=DisplayOrderingChoices.RANDOM,
    )

    ngos = models.ManyToManyField(verbose_name=_("NGOs"), to=Ngo, blank=True, related_name="partners")

    date_created = models.DateTimeField(verbose_name=_("date created"), auto_now_add=timezone.now, editable=False)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), auto_now=timezone.now, editable=False)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")
        constraints = [
            models.UniqueConstraint(Lower("subdomain"), name="subdomain_unique"),
        ]

    def __str__(self):
        return f"{self.name}"
