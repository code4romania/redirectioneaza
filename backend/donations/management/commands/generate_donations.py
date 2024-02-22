import random
import string
from typing import List

from django.core.management import BaseCommand
from faker import Faker
from localflavor.ro.ro_counties import COUNTIES_CHOICES

from donations.models.main import Donor, Ngo

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

        generated_donations: List[Donor] = []
        while len(generated_donations) < total_donations:
            # pick a random NGO
            ngo = ngos[random.randint(0, len(ngos) - 1)]

            # generate a random donor
            donor = Donor(
                ngo=ngo,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                initial=random.choice(string.ascii_uppercase),
                email=fake.email(),
                phone=fake.phone_number(),
                city=fake.city(),
                county=COUNTIES_CHOICES[random.randint(0, len(COUNTIES_CHOICES) - 1)][1],
                income_type="wage",
                has_signed=random.choice([True, False]),
                two_years=random.choice([True, False]),
                pdf_url="https://storage.googleapis.com/redirectioneaza/logo_bw.png",
            )
            donor.set_cnp(fake.ssn())
            donor.set_address_helper(
                street_name=fake.street_name(),
                street_number=fake.building_number(),
                street_bl=random.choice(["", random.randint(1, 20)]),
                street_sc=random.choice(["", random.choice(string.ascii_uppercase)]),
                street_et=random.choice(["", random.randint(1, 20)]),
                street_ap=random.choice(["", random.randint(1, 200)]),
            )

            generated_donations.append(donor)

        self.stdout.write(self.style.SUCCESS("Writing to the database..."))
        Donor.objects.bulk_create(generated_donations, batch_size=10)

        self.stdout.write(self.style.SUCCESS("Done!"))
