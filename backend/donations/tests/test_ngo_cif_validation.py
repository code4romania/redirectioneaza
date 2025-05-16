from django.core.exceptions import ValidationError
from django.test import TestCase

from donations.models.ngos import ngo_id_number_validator


class NgoCIFValidationTests(TestCase):
    def setUp(self):
        self.valid_cifs = (
            "36317167",
            "RO36317167",
        )

        self.invalid_cifs = (
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
        )

    def test_validation_works_with_good_cif(self):
        for cif in self.valid_cifs:
            self.assertEqual(ngo_id_number_validator(cif), None)

    def test_validation_fails_with_broken_cif(self):
        for cif in self.invalid_cifs:
            self.assertRaises(ValidationError, ngo_id_number_validator, cif)
