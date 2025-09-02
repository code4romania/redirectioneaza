import random
from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db import IntegrityError
from donations.models.ngos import Cause, Ngo
from faker import Faker
from localflavor.ro.ro_counties import COUNTIES_CHOICES

fake = Faker("ro_RO")

MOCK_NGO_NAMES = {
    "types": [
        "Asociația",
        "Fundația",
        "Organizația",
        "",
    ],
    "names": [
        # These names were automatically generated using an LLM; while we have manually removed some
        # of the less appropriate names, there may still be some that can be considered offensive
        # or inappropriate. If you find any, please open an issue on GitHub.
        "Acces Medical pentru Toți",
        "Accesibil pentru Toți",
        "Acțiune pentru Schimbare",
        "Acțiune pentru Sănătate Mintală",
        "Ajutor pentru Boli Rare",
        "Ajutor pentru Refugiați",
        "Ajutor pentru Satele Izolate",
        "Ajută Copiii",
        "Artă pentru Incluziune",
        "Asistență Medicală Mobilă",
        "Asistență pentru Persoanele Bolnave de Cancer",
        "Casa Speranței",
        "Copiii Lumii",
        "Copiii Speranței",
        "Copiii Sănătoși",
        "Copiii Împreună",
        "Cărțile Deschise",
        "Drepturile Migranților",
        "Educație Medicală pentru Toți",
        "Educație Plus",
        "Educație pentru Toți",
        "Educație pentru Viitor",
        "Femei Puternice",
        "Grija pentru Sănătatea Maternă",
        "Hrana pentru Toți",
        "Incluziune pentru Toți",
        "Inițiativa pentru Egalitate de Gen",
        "Îmbunătățirea Sănătății Mintale",
        "Împreună pentru Boli Infecțioase",
        "Împreună pentru Drepturile Femeilor",
        "Împreună pentru Sănătate",
        "Împreună pentru Toleranță",
        "Împreună pentru Viață",
        "Înfruntă HIV/SIDA",
        "Îngrijire pentru Bolnavi",
        "Învinge Dependenta",
        "Învinge Diabetul",
        "Învinge Sărăcia",
        "Lupta împotriva Cancerului",
        "ONG-ul Inimii",
        "Oameni și Planeta",
        "Ochi pentru Nevoiași",
        "Prietenii Naturii",
        "Prietenii Planetei",
        "Prietenii Sănătății",
        "Promovarea Vaccinării",
        "Protecția Animalelor Sălbatice",
        "Protecția Copiilor Bolnavi",
        "Protecția Copiilor Rămași Orfani",
        "Protecția Drepturilor Omului",
        "Protecția Sănătății Femeilor",
        "Protecția Sănătății Oculare",
        "Protecția Sănătății Respiratorii",
        "Protecția Victimelor Violenței",
        "Pădurea Vieții",
        "Renașterea Sătească",
        "Salvarea Animalelor",
        "Salvați Flora și Fauna",
        "Salvați Vieți",
        "Solidaritate pentru Oameni În Vârstă",
        "Solidaritate pentru Sănătate",
        "Speranța Vieții",
        "Speranță pentru Orfani",
        "Speranță pentru Sănătate",
        "Sprijin pentru Pacienți",
        "Sprijin pentru Persoanele Fără Adăpost",
        "Sprijin pentru Persoanele cu Boli Cronice",
        "Sprijin pentru Persoanele cu Boli Rare",
        "Sprijin pentru Persoanele cu Dizabilități",
        "Sprijin pentru Persoanele cu Handicap Fizic",
        "Sprijin pentru Victimele Dezastrelor Naturale",
        "Sprijin pentru Viitor",
        "Sprijină Educația",
        "Sprijină Sănătatea",
        "Sănătate pentru Comunitate",
        "Sănătate pentru Oameni în Vârstă",
        "Sănătate pentru Persoanele cu Boli Mintale",
        "Sănătate pentru Persoanele cu Dizabilități",
        "Sănătate pentru Satele Izolate",
        "Un Viitor Mai Verde",
        "Un Zâmbet pentru Bătrânețe",
        "Viitor Luminos",
        "Viitor Sănătos",
    ],
}


class Command(BaseCommand):
    help = "Generate fake Organizations for testing purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "total_orgs",
            type=int,
            help="How many organizations to create",
            default=10,
        )
        parser.add_argument(
            "--valid",
            action="store_true",
            help="Generate only valid, active organizations",
        )
        parser.add_argument(
            "--user_only",
            action="store_true",
            help="Generate only users with no organization",
        )

    def handle(self, *args, **options):
        total_organizations = options["total_orgs"]
        create_valid = options.get("valid", None)
        create_user_only = options.get("user_only", None)

        organizations: List[Dict[str, Any]] = []
        generated_organization_names: List[str] = []

        user_model = get_user_model()

        self.stdout.write(self.style.SUCCESS(f"Generating {total_organizations} organization(s) to the database."))

        consecutive_creation_errors: int = 0
        consecutive_identical_names: int = 0
        while len(organizations) < total_organizations:
            county = COUNTIES_CHOICES[random.randint(0, len(COUNTIES_CHOICES) - 1)][1]
            address = fake.street_address()

            type_ = MOCK_NGO_NAMES["types"][random.randint(0, len(MOCK_NGO_NAMES["types"]) - 1)]
            name_ = MOCK_NGO_NAMES["names"][random.randint(0, len(MOCK_NGO_NAMES["names"]) - 1)]

            org_name = " ".join((type_, name_)).strip()

            if org_name in generated_organization_names:
                consecutive_identical_names += 1
                if consecutive_identical_names > 5:
                    self.stdout.write(
                        self.style.ERROR("Too many consecutive identical names. Aborting and writing to the database.")
                    )
                    break
                continue

            consecutive_identical_names = 0
            generated_organization_names.append(org_name)

            clean_name = org_name.lower().replace('"', "").replace(".", "").replace(",", "").replace("/", "")
            kebab_case_name = (
                "-".join(clean_name.split(" "))
                .replace("ă", "a")
                .replace("â", "a")
                .replace("ș", "s")
                .replace("ț", "t")
                .replace("î", "i")
            )
            owner_email = fake.email()

            try:
                owner = user_model.objects.create_user(
                    email=owner_email,
                    password=owner_email.split("@")[0],
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_verified=random.choice([True, False]),
                )
                owner.save()
            except IntegrityError:
                continue

            should_not_have_ngo = random.choice(range(0, 6)) == 3
            if create_user_only or not create_valid and should_not_have_ngo:
                continue

            organization_details = {
                "name": "Asoc." + org_name,
                "registration_number": fake.vat_id(),
                "address": address,
                "county": county,
                "active_region": county,
                "phone": fake.phone_number(),
                "email": random.choice([owner_email, fake.email()]),
                "website": fake.url(),
                "is_active": create_valid or random.choice([True, False]),
                "is_accepting_forms": create_valid or random.choice([True, False]),
                "ngohub_org_id": random.choice([random.randint(1, 9999), None]),
            }
            try:
                org = Ngo.objects.create(**organization_details)
                org.save()
            except IntegrityError:
                owner.delete()
                continue

            organizations.append(org)

            owner.ngo = org
            owner.save()

            ignore_cause = not create_valid or random.choice(range(0, 6)) == 3

            if ignore_cause:
                continue

            try:
                ngo_cause = Cause.objects.create(
                    ngo=org,
                    is_main=True,
                    allow_online_collection=org.is_accepting_forms or random.choice(range(0, 6)) == 3,
                    slug=kebab_case_name,
                    name=org_name,
                    description=fake.paragraph(nb_sentences=3, variable_nb_sentences=True),
                    bank_account=fake.iban(),
                )
                ngo_cause.save()
            except IntegrityError:
                consecutive_creation_errors += 1
                if consecutive_creation_errors > 5:
                    self.stdout.write(
                        self.style.ERROR("Too many consecutive creation errors. Aborting and writing to the database.")
                    )
                    break
                continue

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(organizations)} organization(s)."))
