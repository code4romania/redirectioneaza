import pytest
from django.core.exceptions import ValidationError

from donations.models.ngos import ngo_id_number_validator


@pytest.mark.django_db
@pytest.mark.parametrize("cif", ["36317167", "RO36317167"])
def test_validation_works_with_good_cif(cif):
    ngo_id_number_validator(cif)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cif",
    [
        # a series of invalid CIFs
        "123456789012",
        "12345678",
        "RO123456789012",
        "RO12345678",
        "1234RO5678",
        # a series of invalid CNPs
        "2520609266176",
        "1790507372858",
        "6040117043197",
        "5010418324902",
        # some random test data
        "XYZ36317167",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    ],
)
def test_validation_fails_with_broken_cif(cif):
    with pytest.raises(ValidationError):
        ngo_id_number_validator(cif)
