from faker import Faker

from donations.models.main import Donor

fake = Faker("ro_RO")


def test_address_encryption():
    fake_address = {
        "street_name": fake.street_name(),
        "street_number": fake.building_number(),
        "street_bl": fake.building_number(),
        "street_sc": fake.building_number(),
        "street_et": fake.building_number(),
        "street_ap": fake.building_number(),
    }

    encrypted_address = Donor.encrypt_address(fake_address)
    decrypted_address = Donor.decrypt_address(encrypted_address)

    assert decrypted_address == fake_address


def test_cnp_encryption():
    fake_cnp: str = fake.unique.ssn()

    encrypted_cnp = Donor.encrypt_cnp(fake_cnp)
    decrypted_cnp = Donor.decrypt_cnp(encrypted_cnp)

    assert decrypted_cnp == fake_cnp
