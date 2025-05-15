import pytest

from donations.models.donors import Donor
from donations.models.ngos import Ngo


@pytest.fixture
def ngo() -> Ngo:
    return Ngo.objects.create(name="Test Ngo")


@pytest.fixture
def donor(ngo) -> Donor:
    return Donor.objects.create(
        f_name="Test",
        l_name="Donor",
        email="test@example.com",
        city="Test City",
        ngo=ngo,
    )
