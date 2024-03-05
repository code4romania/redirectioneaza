import logging

from django.core.management import BaseCommand

from importer.tasks.donor_forms import import_donor_forms

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import donor forms from the old storage but just for Code4Romania (testing this)"

    def handle(self, *args, **options):
        import_donor_forms(filter_by_ngo_slug="code-for-romania")
        self.stdout.write(self.style.SUCCESS("Donor forms import done"))
