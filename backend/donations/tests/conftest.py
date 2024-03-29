import pytest

from donations.models.main import Donor, Ngo


@pytest.fixture
def ngo() -> Ngo:
    return Ngo.objects.create(name="Test Ngo")


@pytest.fixture
def donor(ngo) -> Donor:
    return Donor.objects.create(
        first_name="Test",
        last_name="Donor",
        email="test@example.com",
        city="Test City",
        ngo=ngo,
    )
