import random
import string
from typing import List

from django.core.management import BaseCommand
from django.db import IntegrityError
from faker import Faker

from donations.models.ngos import Ngo
from partners.models import DisplayOrderingChoices, Partner

fake = Faker("ro_RO")


class Command(BaseCommand):
    help = "Generate fake partners"

    def add_arguments(self, parser):
        parser.add_argument(
            "total_partners",
            type=int,
            help="How many partners to create",
            default=5,
        )
        parser.add_argument(
            "--orgs",
            type=int,
            help="Number of organizations to assign to each partner",
            default=None,
        )

    def handle(self, *args, **options):
        total_partners = options["total_partners"]
        num_orgs = options.get("orgs", None)

        errors_threshold = 10

        self.stdout.write(
            f"Generating {total_partners} partners with "
            f"{num_orgs if num_orgs else 'a random number of'} "
            f"organizations each"
        )

        ngos = list(Ngo.active.all())
        if not ngos:
            self.stdout.write("No active NGOs found. Exiting...")
            return

        generated_partners_count = 0
        errors_count = 0

        while generated_partners_count < total_partners and errors_count < errors_threshold:
            num_orgs = num_orgs if num_orgs else random.randint(1, min(15, len(ngos)))

            partner_name = fake.company()
            partner_subdomain = ""
            for letter in partner_name:
                letter = letter.lower()
                if letter in (string.ascii_lowercase + string.digits):
                    partner_subdomain += letter
                else:
                    partner_subdomain += "-"

            try:
                partner = Partner(
                    subdomain=partner_subdomain,
                    name=partner_name,
                    display_ordering=random.choice([c[0] for c in DisplayOrderingChoices.choices]),
                    has_custom_header=random.choice([True, False]),
                    has_custom_note=random.choice([True, False]),
                )
                partner.save()
            except IntegrityError:
                self.stdout.write(f"Duplicate partner with subdomain {partner_subdomain}. Skipping...")
                errors_count += 1
                continue

            partner_ngos: List[Ngo] = random.sample(ngos, num_orgs)
            partner.ngos.add(*partner_ngos)

            generated_partners_count += 1

        self.stdout.write(f"Generated {generated_partners_count} partners")
