from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from django.db import models
from django.utils.timezone import now

from donations.models import Donor, Ngo
from stats.models import Stat


class StatsChoices(models.TextChoices):
    REDIRECTIONS_PER_DAY = "donations_per_day", "Donations per Year and Month"
    NGOS_REGISTERED = "ngos_registered", "Registered NGOs"
    NGOS_ACTIVE = "ngos_active", "Active NGOs"
    NGOS_WITH_NGOHUB = "ngos_with_ngohub", "NGOs with NGO Hub"


def _create_stat_redirections_per_day(for_date: date):
    metric: Decimal = Decimal(Donor.available.filter(date_created__date=for_date).count())
    expiration: Optional[datetime] = now() + timedelta(days=5)
    if for_date < now().date():
        expiration = None

    Stat.objects.update_or_create(
        name=StatsChoices.REDIRECTIONS_PER_DAY,
        date=for_date,
        defaults={
            "value": metric,
            "expires_at": expiration,
        },
    )


def _create_stat_ngos_registered():
    metric: Decimal = Decimal(Ngo.objects.count())
    expiration: datetime = now() + timedelta(minutes=5)

    Stat.objects.update_or_create(
        name=StatsChoices.NGOS_REGISTERED,
        defaults={
            "value": metric,
            "expires_at": expiration,
        },
    )


def _create_stat_ngos_active():
    metric: Decimal = Decimal(Ngo.with_forms_this_year.count())
    expiration: datetime = now() + timedelta(minutes=5)

    Stat.objects.update_or_create(
        name=StatsChoices.NGOS_ACTIVE,
        defaults={
            "value": metric,
            "expires_at": expiration,
        },
    )


def _create_stat_ngos_with_ngohub():
    metric: Decimal = Decimal(Ngo.ngo_hub.count())
    expiration: datetime = now() + timedelta(minutes=5)

    Stat.objects.update_or_create(
        name=StatsChoices.NGOS_WITH_NGOHUB,
        defaults={
            "value": metric,
            "expires_at": expiration,
        },
    )


def create_stat(*, stat_choice: StatsChoices, for_date: date = None) -> None:
    if stat_choice == StatsChoices.REDIRECTIONS_PER_DAY:
        if for_date is None:
            raise ValueError("for_date must be provided for REDIRECTIONS_PER_DAY statistic.")
        _create_stat_redirections_per_day(for_date=for_date)
    elif stat_choice == StatsChoices.NGOS_REGISTERED:
        _create_stat_ngos_registered()
    elif stat_choice == StatsChoices.NGOS_ACTIVE:
        _create_stat_ngos_active()
    elif stat_choice == StatsChoices.NGOS_WITH_NGOHUB:
        _create_stat_ngos_with_ngohub()
