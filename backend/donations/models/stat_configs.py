from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional

from django.db import models
from django.utils.timezone import now

from donations.models import Donor, Ngo
from stats.models import Stat


class StatsChoices(models.TextChoices):
    REDIRECTIONS_PER_DAY = "donations_per_day", "Donations per Year and Month"

    NGOS_REGISTERED = "ngos_registered", "Registered NGOs"
    NGOS_ACTIVE = "ngos_active", "Active NGOs"
    NGOS_WITH_NGOHUB = "ngos_with_ngohub", "NGOs with NGO Hub"

    NGOS_REGISTERED_PER_YEAR = "ngos_registered_per_year", "NGOs Registered per Year"
    NGOS_ACTIVE_PER_YEAR = "ngos_active_per_year", "NGOs Active per Year"
    NGOS_WITH_NGOHUB_PER_YEAR = "ngos_with_ngohub_per_year", "NGOs with NGO Hub per Year"


def _calculate_expiration(
    *,
    delta: Dict[str, int],
    for_date: Optional[date] = None,
) -> Optional[datetime]:
    if for_date < now().date():
        return None

    return now() + timedelta(**delta)


def _save_stat(
    *,
    name: StatsChoices,
    metric: Decimal,
    expiration: Optional[datetime],
    for_date: Optional[date] = None,
) -> None:
    Stat.objects.update_or_create(
        name=name,
        date=for_date,
        defaults={
            "value": metric,
            "expires_at": expiration,
        },
    )


def _create_stat_redirections_per_day(for_date: date):
    metric: Decimal = Decimal(Donor.available.filter(date_created__date=for_date).count())
    expiration: Optional[datetime] = _calculate_expiration(delta={"minutes": 5}, for_date=for_date)

    _save_stat(name=StatsChoices.REDIRECTIONS_PER_DAY, metric=metric, expiration=expiration, for_date=for_date)


def _create_stat_ngos_registered():
    metric: Decimal = Decimal(Ngo.objects.count())
    expiration: datetime = _calculate_expiration(delta={"minutes": 5})

    _save_stat(name=StatsChoices.NGOS_REGISTERED, metric=metric, expiration=expiration)


def _create_stat_ngos_registered_yearly(*, for_date: date):
    metric: Decimal = Decimal(Ngo.objects.filter(date_created__year=for_date.year).count())
    expiration: datetime = _calculate_expiration(delta={"minutes": 15}, for_date=for_date)

    _save_stat(name=StatsChoices.NGOS_REGISTERED_PER_YEAR, metric=metric, expiration=expiration, for_date=for_date)


def _create_stat_ngos_active():
    metric: Decimal = Decimal(Ngo.with_forms_this_year.count())
    expiration: datetime = _calculate_expiration(delta={"minutes": 5})

    _save_stat(name=StatsChoices.NGOS_ACTIVE, metric=metric, expiration=expiration)


def _create_stat_ngos_active_yearly(*, for_date: date):
    metric: Decimal = Decimal(
        len((Donor.available.filter(date_created__year=for_date.year).values("ngo_id").distinct()))
    )
    expiration: datetime = _calculate_expiration(delta={"minutes": 15}, for_date=for_date)

    _save_stat(name=StatsChoices.NGOS_ACTIVE_PER_YEAR, metric=metric, expiration=expiration, for_date=for_date)


def _create_stat_ngos_with_ngohub():
    metric: Decimal = Decimal(Ngo.ngo_hub.count())
    expiration: datetime = _calculate_expiration(delta={"minutes": 5})

    _save_stat(name=StatsChoices.NGOS_WITH_NGOHUB, metric=metric, expiration=expiration)


def _create_stat_ngos_with_ngohub_yearly(*, for_date: date):
    metric: Decimal = Decimal(Ngo.ngo_hub.filter(date_created__year=for_date.year).count())
    expiration: datetime = _calculate_expiration(delta={"minutes": 15}, for_date=for_date)

    _save_stat(name=StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR, metric=metric, expiration=expiration, for_date=for_date)


def create_stat(*, stat_choice: StatsChoices, for_date: date = None) -> None:
    if stat_choice in (
        StatsChoices.REDIRECTIONS_PER_DAY,
        StatsChoices.NGOS_REGISTERED_PER_YEAR,
        StatsChoices.NGOS_ACTIVE_PER_YEAR,
        StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR,
    ):
        if for_date is None:
            raise ValueError("for_date must be provided for time-specific statistics.")

        if stat_choice == StatsChoices.REDIRECTIONS_PER_DAY:
            _create_stat_redirections_per_day(for_date=for_date)
        elif stat_choice == StatsChoices.NGOS_REGISTERED_PER_YEAR:
            _create_stat_ngos_registered_yearly(for_date=for_date)
        elif stat_choice == StatsChoices.NGOS_ACTIVE_PER_YEAR:
            _create_stat_ngos_active_yearly(for_date=for_date)
        elif stat_choice == StatsChoices.NGOS_WITH_NGOHUB_PER_YEAR:
            _create_stat_ngos_with_ngohub_yearly(for_date=for_date)
    elif stat_choice == StatsChoices.NGOS_REGISTERED:
        _create_stat_ngos_registered()
    elif stat_choice == StatsChoices.NGOS_ACTIVE:
        _create_stat_ngos_active()
    elif stat_choice == StatsChoices.NGOS_WITH_NGOHUB:
        _create_stat_ngos_with_ngohub()
