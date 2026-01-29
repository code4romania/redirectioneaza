from django.test import TestCase
from faker import Faker

from donations.models import Cause, Donor, Ngo
from donations.tests.builder import DonorTestBuilder

faker = Faker("ro_RO")


class DonorAnonymizationTestCase(TestCase):
    def setUp(self):
        self.ngo = Ngo.objects.create(
            name="Test NGO",
            registration_number=faker.vat_id(),
            address="123 Test St, Test City",
        )
        self.cause = Cause.objects.create(
            ngo=self.ngo,
            name="Test Cause",
            description="A cause for testing purposes.",
        )

    def test_full_donor_anonymization(self):
        donor: Donor = DonorTestBuilder(cause=self.cause).with_all_fields().build()

        self.assertNotEqual(donor.f_name, "")
        self.assertNotEqual(donor.l_name, "")
        self.assertNotEqual(donor.initial, "")
        self.assertNotEqual(donor.get_cnp(), "")

        self.assertNotEqual(donor.city, "")
        self.assertNotEqual(donor.county, "")
        self.assertNotEqual(donor.get_address(), {})

        self.assertNotEqual(donor.phone, "")
        self.assertNotEqual(donor.email, "")

        self.assertNotEqual(donor.geoip, {})

        self.assertNotEqual(donor.pdf_file.name, "")

        self.assertIsNone(donor.personal_data_removal_started_at)
        self.assertIsNone(donor.personal_data_removed_at)

        donor.remove_personal_data()

        donor.refresh_from_db()

        self.assertEqual(donor.f_name, "")
        self.assertEqual(donor.l_name, "")
        self.assertEqual(donor.initial, "")
        self.assertEqual(donor.get_cnp(), "")

        self.assertNotEqual(donor.city, "")
        self.assertNotEqual(donor.county, "")
        self.assertEqual(donor.get_address(), {})

        self.assertEqual(donor.phone, "")
        self.assertEqual(donor.email, "")

        self.assertEqual(donor.geoip, {})

        self.assertEqual(donor.pdf_file.name, "")

        self.assertIsNotNone(donor.personal_data_removal_started_at)
        self.assertIsNotNone(donor.personal_data_removed_at)
