import random
from typing import list

from django.core.management import BaseCommand
from django.db import IntegrityError
from django.utils.text import slugify
from faker import Faker

from donations.models.ngos import Cause
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
        num_causes = options.get("orgs", None)

        errors_threshold = 10

        self.stdout.write(
            f"Generating {total_partners} partners with "
            f"{num_causes if num_causes else 'a random number of'} "
            f"organizations each"
        )

        causes = list(Cause.public_active.all())
        if not causes:
            self.stdout.write("No active Causes found. Exiting...")
            return

        generated_partners_count = 0
        errors_count = 0

        while generated_partners_count < total_partners and errors_count < errors_threshold:
            num_causes = num_causes if num_causes else random.randint(1, min(15, len(causes)))

            partner_name = fake.company()
            partner_subdomain = slugify(partner_name)

            try:
                partner = Partner(
                    subdomain=partner_subdomain,
                    name=partner_name,
                    display_ordering=random.choice([c[0] for c in DisplayOrderingChoices.choices]),
                    custom_cta=random.choice(["", fake.text(max_nb_chars=50)]),
                    has_custom_header=random.choice([True, False]),
                    has_custom_note=random.choice([True, False]),
                )
                partner.save()
            except IntegrityError:
                self.stdout.write(f"Duplicate partner with subdomain {partner_subdomain}. Skipping...")
                errors_count += 1
                continue

            partner_causes: list[Cause] = random.sample(causes, num_causes)
            partner.causes.add(*partner_causes, through_defaults={"display_order": 1})

            generated_partners_count += 1

        self.stdout.write(f"Generated {generated_partners_count} partners")
