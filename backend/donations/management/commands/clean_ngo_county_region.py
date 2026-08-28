from django.core.management import BaseCommand
from django.db.models import QuerySet

from donations.models.ngos import Ngo


class Command(BaseCommand):
    help = "Clean up the county and active_region for all NGOs. Move from S1-6 to București"

    def handle(self, *args, **options):
        sector_range: list[int] = list(range(1, 7))
        affected_ngos_region: QuerySet[Ngo] = Ngo.objects.filter(active_region__in=sector_range)
        for ngo in affected_ngos_region:
            ngo.active_region = "București"
            ngo.save()

        self.stdout.write(self.style.SUCCESS(f"Moved {len(affected_ngos_region)} NGOs from S1-6 to București region."))

        affected_ngos_county: QuerySet[Ngo] = Ngo.objects.filter(county__in=sector_range)
        for ngo in affected_ngos_county:
            ngo.locality = f"Sector {ngo.county}"
            ngo.county = "București"
            ngo.save()

        self.stdout.write(self.style.SUCCESS(f"Moved {len(affected_ngos_county)} NGOs from S1-6 to București county."))
