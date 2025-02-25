import random
import string
from typing import List

from django.core.files import File
from django.core.management import BaseCommand
from faker import Faker

from donations.models.donors import Donor
from donations.models.ngos import Ngo
from donations.pdf import create_full_pdf
from redirectioneaza.settings import FORM_COUNTIES_WITH_SECTORS_CHOICES

fake = Faker("ro_RO")


class Command(BaseCommand):
    help = "Generate fake donation forms"

    def add_arguments(self, parser):
        parser.add_argument(
            "total_donations",
            type=int,
            help="How many donations to create",
            default=10,
        )
        parser.add_argument(
            "--org",
            type=int,
            help="The ID of the organization to generate donations for",
            default=None,
        )

    def handle(self, *args, **options):
        total_donations = options["total_donations"]
        target_org = options.get("org", None)

        self.stdout.write(f"Generating {total_donations} donations")

        if not target_org:
            ngos = list(Ngo.active.all())
        else:
            ngos = [Ngo.objects.get(id=target_org)]

        if not ngos:
            self.stdout.write(self.style.ERROR("No active organizations found"))
            return

        generated_donations: List[Donor] = []
        while len(generated_donations) < total_donations:
            # pick a random NGO
            ngo = ngos[random.randint(0, len(ngos) - 1)]
            cnp = fake.ssn()

            address = {
                "street_name": fake.street_name(),
                "street_number": fake.building_number(),
                "street_bl": random.choice(["", random.randint(1, 20)]),
                "street_sc": random.choice(["", random.choice(string.ascii_uppercase)]),
                "street_et": random.choice(["", random.randint(1, 20)]),
                "street_ap": random.choice(["", random.randint(1, 200)]),
            }

            # generate a random donor
            donor = Donor(
                ngo=ngo,
                f_name=fake.first_name(),
                l_name=fake.last_name(),
                initial=random.choice(string.ascii_uppercase),
                email=fake.email(),
                phone=fake.phone_number(),
                city=fake.city(),
                county=FORM_COUNTIES_WITH_SECTORS_CHOICES[
                    random.randint(0, len(FORM_COUNTIES_WITH_SECTORS_CHOICES) - 1)
                ][1],
                income_type="wage",
                has_signed=random.choice([True, False]),
                two_years=random.choice([True, False]),
            )
            donor.set_cnp(cnp)
            donor.set_address_helper(**address)

            donor.pdf_file = File(create_full_pdf(donor))

            generated_donations.append(donor)

        self.stdout.write(self.style.SUCCESS("Writing to the database..."))
        Donor.objects.bulk_create(
            generated_donations,
            batch_size=500,
            ignore_conflicts=True,
        )

        self.stdout.write(self.style.SUCCESS("Done!"))
