import random
import string

from django.core.management import BaseCommand
from django.db.models import QuerySet
from django_q.tasks import async_task
from faker import Faker

import redirectioneaza.settings.locations
from donations.models import Cause
from donations.models.donors import Donor
from donations.models.ngos import Ngo
from donations.pdf import create_full_pdf

fake = Faker("ro_RO")


def _generate_pdf_for_donor(donor_pk: int):
    selected_donor: Donor = Donor.objects.get(pk=donor_pk)
    selected_donor.pdf_file = create_full_pdf(selected_donor)
    selected_donor.save()


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
        parser.add_argument(
            "--no-pdf",
            action="store_true",
            help="Do not generate PDFs for the donations",
            default=False,
        )
        parser.add_argument(
            "--pdf-only",
            action="store_true",
            help="Only generate PDFs for donations without PDFs",
            default=False,
        )

    def handle(self, *args, **options):
        def _generate_pdfs_for_donations(new_donors: QuerySet[Donor]):
            generated_pdfs: int = 0
            self.stdout.write(f"Queuing PDF generation for {new_donors.count()} new donors...")
            for new_donor in new_donors:
                generated_pdfs += 1
                async_task(
                    _generate_pdf_for_donor,
                    new_donor.pk,
                )

                if generated_pdfs % 50 == 0:
                    self.stdout.write(f"Queued {generated_pdfs} / {new_donors.count()} PDFs...")

        batch_size = 200

        pdf_only = options["pdf_only"]
        if pdf_only:
            donors_without_pdfs: QuerySet[Donor] = Donor.objects.filter(pdf_file="")
            self.stdout.write(f"Generating PDFs for {donors_without_pdfs.count()} donations without PDFs...")
            _generate_pdfs_for_donations(donors_without_pdfs)
            self.stdout.write(self.style.SUCCESS("Done!"))
            return

        total_donations = options["total_donations"]
        create_pdf = not options["no_pdf"]
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
        total_generated = 0
        while total_generated < total_donations:
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

            generated_donations.append(donor)
            total_generated += 1

            if len(generated_donations) % 50 == 0:
                self.stdout.write(f"Generated {total_generated} / {total_donations} donations...")

            if len(generated_donations) > batch_size:
                self.stdout.write(f"Writing {len(generated_donations)} donations to the database...")
                Donor.objects.bulk_create(
                    generated_donations,
                    ignore_conflicts=True,
                )
                generated_donations = []

                if create_pdf:
                    _generate_pdfs_for_donations(Donor.objects.filter(pdf_file=""))

        self.stdout.write(
            self.style.SUCCESS(f"Writing the last {len(generated_donations)} donations to the database...")
        )
        Donor.objects.bulk_create(
            generated_donations,
            ignore_conflicts=True,
        )

        self.stdout.write(self.style.SUCCESS("Done!"))
