from django.test import TestCase
from faker import Faker

from donations.models.donors import Donor


class DonorEncryptionTests(TestCase):
    def setUp(self):
        self.faker = Faker("ro_RO")

    def test_address_encryption(self):
        fake_address = {
            "street_name": self.faker.street_name(),
            "street_number": self.faker.building_number(),
            "street_bl": self.faker.building_number(),
            "street_sc": self.faker.building_number(),
            "street_et": self.faker.building_number(),
            "street_ap": self.faker.building_number(),
        }

        encrypted_address = Donor.encrypt_address(fake_address)
        decrypted_address = Donor.decrypt_address(encrypted_address)

        self.assertEqual(decrypted_address, fake_address)

    def test_cnp_encryption(self):
        fake_cnp: str = self.faker.unique.ssn()

        encrypted_cnp = Donor.encrypt_cnp(fake_cnp)
        decrypted_cnp = Donor.decrypt_cnp(encrypted_cnp)

        self.assertEqual(decrypted_cnp, fake_cnp)
