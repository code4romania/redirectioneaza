import random
from typing import Any

from django.core.files import File
from faker import Faker

from donations.models import Cause, Donor
from donations.pdf import create_full_pdf

faker = Faker("ro_RO")


class DonorTestBuilder:
    def __init__(self, *, cause: Cause, is_available: bool = True) -> None:
        self.donor_data: dict[str, Any] = {
            "cause": cause,
            "ngo": cause.ngo,
            "is_available": is_available,
        }

    def build(self) -> Donor:
        donor_data: dict = self.donor_data.copy()

        address: dict | None = donor_data.pop("address", None)
        cnp: str | None = donor_data.pop("cnp", None)

        donor: Donor = Donor(**donor_data)

        if address is not None:
            donor.set_address_helper(**address)
        if cnp is not None:
            donor.set_cnp(cnp)

        donor.save()

        pdf = create_full_pdf(donor)
        donor.pdf_file.save(f"donor_{donor.pk}.pdf", File(pdf))

        return donor

    def with_all_fields(self) -> "DonorTestBuilder":
        return (
            self.with_first_name()
            .with_last_name()
            .with_initial()
            .with_cnp()
            .with_city()
            .with_county()
            .with_address()
            .with_phone()
            .with_email()
            .with_geoip()
            .with_misc()
        )

    def with_first_name(self, first_name: str = None) -> "DonorTestBuilder":
        self.donor_data["f_name"] = first_name if first_name else faker.first_name()

        return self

    def with_last_name(self, last_name: str = None) -> "DonorTestBuilder":
        self.donor_data["l_name"] = last_name if last_name else faker.last_name()

        return self

    def with_initial(self, initial: str = None) -> "DonorTestBuilder":
        self.donor_data["initial"] = initial if initial else faker.random_uppercase_letter()

        return self

    def with_cnp(self, cnp: str = None) -> "DonorTestBuilder":
        self.donor_data["cnp"] = cnp if cnp else faker.ssn()

        return self

    def with_city(self, city: str = None) -> "DonorTestBuilder":
        self.donor_data["city"] = city if city else faker.city()

        return self

    def with_county(self, county: str = None) -> "DonorTestBuilder":
        self.donor_data["county"] = county if county else faker.state()

        return self

    def with_address(self, address: dict[str, str] = None) -> "DonorTestBuilder":
        if address is None:
            address = {
                "street_name": faker.street_name(),
                "street_number": faker.building_number(),
            }
            if faker.boolean(chance_of_getting_true=40):
                address["street_bl"] = faker.building_number()
            if faker.boolean(chance_of_getting_true=40):
                address["street_sc"] = faker.building_number()
            if faker.boolean(chance_of_getting_true=40):
                address["street_et"] = faker.building_number()
            if faker.boolean(chance_of_getting_true=40):
                address["street_ap"] = faker.building_number()

        self.donor_data["address"] = address

        return self

    def with_phone(self, phone: str = None) -> "DonorTestBuilder":
        self.donor_data["phone"] = phone if phone else faker.phone_number()

        return self

    def with_email(self, email: str = None) -> "DonorTestBuilder":
        self.donor_data["email"] = email if email else faker.email()

        return self

    def with_geoip(self, geoip: dict[str, Any] = None) -> "DonorTestBuilder":
        if geoip is None:
            geoip = {
                "ip": faker.ipv4(),
                "country": faker.country(),
                "city": faker.city(),
                "latitude": float(faker.latitude()),
                "longitude": float(faker.longitude()),
            }

        self.donor_data["geoip"] = geoip

        return self

    def with_misc(
        self,
        *,
        is_anonymous: bool = None,
        anaf_gdpr: bool = None,
        two_years: bool = None,
        has_signed: bool = None,
        income_type: str = None,
    ):
        if is_anonymous is None:
            is_anonymous = random.choice([True, False])
        if anaf_gdpr is None:
            anaf_gdpr = random.choice([True, False])
        if two_years is None:
            two_years = random.choice([True, False])
        if has_signed is None:
            has_signed = random.choice([True, False])
        if income_type is None:
            income_type = random.choice(["wage", "pension"])

        misc_data: dict[str, bool | str] = {
            "is_anonymous": is_anonymous,
            "anaf_gdpr": anaf_gdpr,
            "two_years": two_years,
            "has_signed": has_signed,
            "income_type": income_type,
        }
        self.donor_data.update(misc_data)

        return self
