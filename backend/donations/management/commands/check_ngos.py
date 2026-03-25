from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Check NGOs in ANAF Cult Registry"

    def handle(self, *args, **options):
        print("TODO: check NGOs")
