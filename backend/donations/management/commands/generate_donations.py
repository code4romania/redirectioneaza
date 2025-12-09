import random
import string

from django.core.files import File
from django.core.management import BaseCommand
from faker import Faker

import redirectioneaza.settings.locations
from donations.models import Cause
from donations.models.donors import Donor
from donations.models.ngos import Ngo
from donations.pdf import create_full_pdf

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

        if target_org:
            ngos = [Ngo.objects.get(id=target_org)]
        else:
            ngos = list(Ngo.active.all())

        log_message = f"Generating {total_donations} donations"
        if target_org:
            log_message += f" for organization {ngos[0].pk}: '{ngos[0]}'"
        else:
            log_message += f" for {len(ngos)} organizations"
        self.stdout.write(log_message)

        if not ngos:
            self.stdout.write(self.style.ERROR("No active organizations found"))
            return

        generated_donations: list[Donor] = []
        while len(generated_donations) < total_donations:
            # pick a random NGO
            ngo: Ngo = random.choice(ngos)
            if not ngo.causes.exists():
                continue

            cause: Cause = random.choice(ngo.causes.all())
            cnp: str = fake.ssn()

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
                cause=cause,
                f_name=fake.first_name(),
                l_name=fake.last_name(),
                initial=random.choice(string.ascii_uppercase),
                email=fake.email(),
                phone=fake.phone_number(),
                city=fake.city(),
                county=random.choice(redirectioneaza.settings.locations.COUNTIES_WITH_SECTORS_LIST + list(range(1, 7))),
                income_type="wage",
                is_anonymous=random.choice([True, False]),
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
