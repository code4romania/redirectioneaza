import pytest

from donations.models.donors import Donor
from donations.models.ngos import Ngo, Cause


@pytest.fixture
def ngo() -> Ngo:
    return Ngo.objects.create(name="Test Ngo", registration_number="12345678")


@pytest.fixture
def cause(ngo) -> Cause:
    return Cause.objects.create(ngo=ngo, name="Test Cause", slug="test-cause", bank_account="RO123123")


@pytest.fixture
def donor(ngo) -> Donor:
    return Donor.objects.create(
        f_name="Test",
        l_name="Donor",
        email="test@example.com",
        city="Test City",
        ngo=ngo,
    )
