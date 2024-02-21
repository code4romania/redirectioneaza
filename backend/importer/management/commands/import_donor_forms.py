import logging

from django.core.management import BaseCommand

from importer.tasks.donor_forms import import_donor_forms

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import donor forms from the old storage"

    def handle(self, *args, **options):
        import_donor_forms()
        self.stdout.write(self.style.SUCCESS("Donor forms import done"))
