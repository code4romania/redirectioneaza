import random

from django.core.management import BaseCommand
from django.db import IntegrityError
from faker import Faker

from donations.models.ngos import Cause, CauseVisibilityChoices, Ngo

fake = Faker("ro_RO")

MOCK_CAUSE_NAMES = {
    "titles": [
        # These names were automatically generated using an LLM; while we have manually removed some
        # of the less appropriate names, there may still be some that can be considered offensive
        # or inappropriate. If you find any, please open an issue on GitHub.
        "Ajută-l pe {name} să lupte",
        "Ajută-l pe {name} să meargă",
        "Ajută-l pe {name} să respire",
        "Ajută-l pe {name} să vadă",
        "Ajută-l pe {name}",
        "Alături de {name} în lupta cu boala",
        "Dragoste pentru bătrânii singuri",
        "Eroii lui {name}",
        "Fiecare zi contează pentru {name}",
        "Fii alături de {name}",
        "Fii alături de {name}",
        "Fii eroul lui {name}",
        "Fără durere pentru {name}",
        "Hai să-l ajutăm pe {name}",
        "Lumina pentru {name}",
        "Mai mult timp pentru {name}",
        "Mediu curat pentru generațiile viitoare",
        "Mediu curat pentru viitor",
        "O inimă puternică pentru {name}",
        "O lume mai bună pentru {name}",
        "O mână de ajutor pentru {name}",
        "O viață normală pentru {name}",
        "O șansă la viață pentru {name}",
        "O șansă pentru {name}",
        "Pentru sănătatea lui {name}",
        "Redăm vederea lui {name}",
        "Salvează-l pe {name}",
        "Salvăm visul lui {name}",
        "Speranță pentru {name}",
        "Speranță pentru {name}",
        "Speranță pentru {name}",
        "Sprijin pentru familia lui {name}",
        "Sprijin pentru {name}",
        "Sprijin pentru {name}",
        "Susținem educația copiilor din medii defavorizate",
        "Susținem lupta lui {name}",
        "Susținem recuperarea lui {name}",
        "Susținere pentru {name}",
        "Să-i redăm speranța lui {name}",
        "Să-l ajutăm pe {name} să crească mare",
        "Să-l ajutăm pe {name}",
        "Să-l ajutăm pe {name}",
        "Să-l ajutăm pe {name}",
        "Să-l sprijinim pe {name}",
        "Timp prețios pentru {name}",
        "Un adăpost pentru {name} și familia lui",
        "Un cămin pentru {name} și familia lui",
        "Un miracol pentru {name}",
        "Un nou început pentru {name}",
        "Un nou început pentru {name}",
        "Un spital mai bun pentru copii",
        "Un transplant pentru {name}",
        "Un transplant pentru {name}",
        "Un tratament pentru {name}",
        "Un viitor pentru {name}",
        "Un viitor pentru {name}",
        "Un zâmbet pentru {name}",
        "Viață lungă pentru {name}",
        "Viață pentru {name}",
        "Zâmbetul lui {name}",
        "{name} are nevoie de noi",
        "{name} are nevoie de noi",
        "{name} are nevoie de noi",
        "{name} are nevoie de o operație",
        "{name} are nevoie de sprijin",
        "{name} are nevoie de tratament",
        "{name} are nevoie de tratament",
        "{name} are nevoie de un transplant",
        "{name} merită o copilărie",
        "{name} merită o șansă",
        "{name} merită o șansă",
        "{name} merită să alerge",
        "{name} merită să fie fericit",
        "{name} nu renunță la visul lui",
        "{name} nu renunță",
        "{name} nu trebuie să renunțe",
        "{name} trebuie să lupte",
        "{name} trebuie să lupte",
        "{name} trebuie să trăiască",
        "{name} trebuie să învingă",
        "{name} vrea să meargă din nou",
        "{name} vrea să meargă din nou",
        "{name} vrea să trăiască",
        "Îi dăruim viață lui {name}",
        "Îi oferim lui {name} o șansă la educație",
        "Îl ajutăm pe {name} să vadă din nou",
        "Îl ajutăm pe {name}",
        "Îl salvăm pe {name}",
        "Îl salvăm pe {name}",
        "Îl salvăm pe {name}",
        "Îl sprijinim pe {name}",
        "Îl sprijinim pe {name}",
        "Îl susținem pe {name}",
        "Îl susținem pe {name}",
        "Împreună pentru o lume mai bună",
        "Împreună pentru sănătatea lui {name}",
        "Împreună pentru {name}",
        "Împreună pentru {name}",
        "Împreună pentru {name}",
        "Împreună pentru {name}",
    ],
    "names": [
        "Adela",
        "Adriana",
        "Adriana",
        "Alexandru",
        "Alina",
        "Amalia",
        "Ana",
        "Anca",
        "Andrei",
        "Anisia",
        "Anton",
        "Augustin",
        "Bianca",
        "Bogdan",
        "Camelia",
        "Carmen",
        "Cerasela",
        "Ciprian",
        "Claudia",
        "Claudiu",
        "Cosmin",
        "Cristian",
        "Cristina",
        "Cătălin",
        "Damian",
        "Daniel",
        "Darius",
        "Denis",
        "Diana",
        "Doina",
        "Dragoș",
        "Eduard",
        "Elena",
        "Emanuel",
        "Emilia",
        "Emilian",
        "Eric",
        "Estera",
        "Eugen",
        "Evelina",
        "Felicia",
        "Felix",
        "Flavia",
        "Florin",
        "Gabriel",
        "Gabriela",
        "Gelu",
        "George",
        "Georgiana",
        "Horia",
        "Ilinca",
        "Ioana",
        "Ionuț",
        "Izabela",
        "Larisa",
        "Laurențiu",
        "Lavinia",
        "Lidia",
        "Loredana",
        "Lucian",
        "Luiza",
        "Magda",
        "Marcel",
        "Maria",
        "Marina",
        "Matei",
        "Melania",
        "Mihaela",
        "Mihai",
        "Miruna",
        "Nicolae",
        "Nicoleta",
        "Oana",
        "Octavian",
        "Ovidiu",
        "Paul",
        "Petru",
        "Radu",
        "Raluca",
        "Rareș",
        "Raul",
        "Robert",
        "Roxana",
        "Sabina",
        "Sebastian",
        "Silviu",
        "Simona",
        "Sorin",
        "Sorina",
        "Stela",
        "Teodora",
        "Tiberiu",
        "Tudor",
        "Valentin",
        "Veronica",
        "Victor",
        "Violeta",
        "Viorica",
        "Vlad",
        "Ștefan",
    ],
}


class Command(BaseCommand):
    help = "Generate fake Causes for testing purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "total_causes",
            type=int,
            help="How many causes to create",
            default=10,
        )
        parser.add_argument(
            "--org",
            type=int,
            help="The ID of the organization to which the causes should be associated",
        )
        parser.add_argument(
            "--visible",
            action="store_true",
            help="Generate only visible causes",
        )

    def handle(self, *args, **options):
        total_causes = options["total_causes"]
        target_org_id = options.get("org", None)
        create_visible = options.get("visible", None)

        causes: list[Cause] = []
        generated_cause_names: list[str] = []

        self.stdout.write(self.style.SUCCESS(f"Generating {total_causes} cause(s) to the database."))

        target_org = None
        if target_org_id:
            target_org = Ngo.objects.get(pk=target_org_id)

        consecutive_identical_names: int = 0
        while len(causes) < total_causes:
            if target_org:
                ngo: Ngo = target_org
            else:
                ngo: Ngo = Ngo.active.order_by("?").first()
                if not ngo.can_create_causes:
                    continue

            cause_title = MOCK_CAUSE_NAMES["titles"][random.randint(0, len(MOCK_CAUSE_NAMES["titles"]) - 1)]
            name_in_cause = MOCK_CAUSE_NAMES["names"][random.randint(0, len(MOCK_CAUSE_NAMES["names"]) - 1)]

            # noinspection StrFormat
            cause_name = cause_title.format(name=name_in_cause)

            if cause_name in generated_cause_names:
                consecutive_identical_names += 1
                if consecutive_identical_names > 5:
                    self.stdout.write(
                        self.style.ERROR("Too many consecutive identical names. Aborting and writing to the database.")
                    )
                    break
                continue

            consecutive_identical_names = 0
            generated_cause_names.append(cause_name)

            clean_name = cause_name.lower().replace('"', "").replace(".", "").replace(",", "").replace("/", "")
            kebab_case_name = (
                "-".join(clean_name.split(" "))
                .replace("ă", "a")
                .replace("â", "a")
                .replace("ș", "s")
                .replace("ț", "t")
                .replace("î", "i")
            )

            visibility = CauseVisibilityChoices.PUBLIC
            if not create_visible:
                visibility = random.choice(
                    [
                        CauseVisibilityChoices.PUBLIC,
                        CauseVisibilityChoices.UNLISTED,
                        CauseVisibilityChoices.PRIVATE,
                    ]
                )

            allow_online_collection = (
                ngo.has_online_tax_account if not ngo.has_online_tax_account else random.choice(range(0, 6)) == 3
            )
            causes.append(
                Cause(
                    ngo=ngo,
                    is_main=False,
                    visibility=visibility,
                    allow_online_collection=allow_online_collection,
                    slug=kebab_case_name,
                    name=cause_name,
                    description=fake.paragraph(nb_sentences=random.randint(1, 3), variable_nb_sentences=True),
                    bank_account=fake.iban(),
                )
            )

        try:
            self.stdout.write(self.style.SUCCESS(f"Writing {len(causes)} cause(s) to the database."))
            Cause.objects.bulk_create(causes, ignore_conflicts=True)
        except IntegrityError:
            pass

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(causes)} causes(s)."))
