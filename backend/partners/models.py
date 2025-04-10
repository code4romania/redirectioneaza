from typing import Dict

from django.db import models
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Cause, Ngo
from redirectioneaza.common.validators import url_validator


class DisplayOrderingChoices(models.TextChoices):
    CUSTOM = "CST", _("Custom")

    ALPHABETICAL = "ABC", _("Alphabetical")
    ALPHABETICAL_REVERSE = "CBA", _("Alphabetical (reverse)")

    NEWEST = "AGE", _("Newest")
    OLDEST = "OLD", _("Oldest")

    RANDOM = ("RND", _("Random"))


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

    ngos = models.ManyToManyField(
        verbose_name=_("NGOs"),
        to=Ngo,
        through="PartnerNgo",
        blank=True,
        related_name="partners",
    )
    causes = models.ManyToManyField(
        verbose_name=_("Causes"),
        to=Cause,
        through="PartnerCause",
        blank=True,
        related_name="partners",
    )

    date_created = models.DateTimeField(verbose_name=_("date created"), auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(verbose_name=_("date updated"), auto_now=True, editable=False)

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

    def ordered_causes(self) -> QuerySet[Cause]:
        display_ordering_mapping: Dict[str, str] = {
            str(DisplayOrderingChoices.ALPHABETICAL): "name",
            str(DisplayOrderingChoices.ALPHABETICAL_REVERSE): "-name",
            str(DisplayOrderingChoices.OLDEST): "date_created",
            str(DisplayOrderingChoices.NEWEST): "-date_created",
            str(DisplayOrderingChoices.CUSTOM): "partner_causes__display_order",
        }

        order: str = display_ordering_mapping.get(self.display_ordering, "?")

        # noinspection PyTypeChecker
        return self.causes.order_by(order).all()

    def ordered_ngos(self) -> QuerySet[Ngo]:
        display_ordering_mapping: Dict[str, str] = {
            str(DisplayOrderingChoices.ALPHABETICAL): "name",
            str(DisplayOrderingChoices.ALPHABETICAL_REVERSE): "-name",
            str(DisplayOrderingChoices.OLDEST): "date_created",
            str(DisplayOrderingChoices.NEWEST): "-date_created",
            str(DisplayOrderingChoices.CUSTOM): "partner_ngos__display_order",
        }

        order: str = display_ordering_mapping.get(self.display_ordering, "?")

        # noinspection PyTypeChecker
        return self.ngos.order_by(order).all()

    def initialize_custom_display_ordering(self):
        partner_causes = PartnerCause.objects.filter(partner=self).order_by("display_order", "pk")

        for index, partner_cause in enumerate(partner_causes):
            partner_cause.display_order = index + 1
            partner_cause.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.display_ordering == DisplayOrderingChoices.CUSTOM:
            self.initialize_custom_display_ordering()


class PartnerNgo(models.Model):
    partner = models.ForeignKey(
        verbose_name=_("partner"),
        to=Partner,
        on_delete=models.CASCADE,
        related_name="partner_ngos",
    )
    ngo = models.ForeignKey(
        verbose_name=_("NGO"),
        to=Ngo,
        on_delete=models.CASCADE,
        related_name="partner_ngos",
    )

    display_order = models.PositiveIntegerField(verbose_name=_("display order"), default=0)

    class Meta:
        verbose_name = _("Partner NGO")
        verbose_name_plural = _("Partner NGOs")
        constraints = [
            models.UniqueConstraint(fields=["partner", "ngo"], name="partner_ngo_unique"),
        ]

    def __str__(self):
        return f"{self.partner} - {self.ngo}"

    def save(self, *args, **kwargs):
        if self.display_order == 0:
            number_of_partner_ngos = PartnerNgo.objects.filter(partner=self.partner).count()
            self.display_order = number_of_partner_ngos + 1

        super().save(*args, **kwargs)


class PartnerCause(models.Model):
    partner = models.ForeignKey(
        verbose_name=_("partner"),
        to=Partner,
        on_delete=models.CASCADE,
        related_name="partner_causes",
    )
    cause = models.ForeignKey(
        verbose_name=_("Cause"),
        to=Cause,
        on_delete=models.CASCADE,
        related_name="partner_causes",
    )

    display_order = models.PositiveIntegerField(verbose_name=_("display order"), default=0)

    class Meta:
        verbose_name = _("Partner Cause")
        verbose_name_plural = _("Partner Causes")
        constraints = [
            models.UniqueConstraint(fields=["partner", "cause"], name="partner_cause_unique"),
        ]

    def __str__(self):
        return f"{self.partner} - {self.cause}"

    def save(self, *args, **kwargs):
        if self.display_order == 0:
            number_of_partner_causes = PartnerCause.objects.filter(partner=self.partner).count()
            self.display_order = number_of_partner_causes + 1

        super().save(*args, **kwargs)
