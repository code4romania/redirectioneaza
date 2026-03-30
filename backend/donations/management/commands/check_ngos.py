from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone

from donations.models.ngos import Ngo
from donations.workers.check_organization import cult_registry_check_organizations


class Command(BaseCommand):
    help = "Check NGOs in ANAF Cult Registry"

    def handle(self, *args, **options):
        long_deadline = timezone.now() - timezone.timedelta(days=90)
        recent_deadline = timezone.now() - timezone.timedelta(hours=1)
        short_deadline = timezone.now() - timezone.timedelta(days=30)

        registration_numbers = set(
            Ngo.objects.exclude(pause_cult_registry_check=True).filter(registration_number_valid=True)
            .filter(
                # ASAP check NGOs which are were not yet checked in the registry:
                Q(Q(is_in_cult_registry__isnull=True) & Q(cult_registry_check_started__isnull=True))
                # ASAP check NGOs which were scheduled in the past but the check did not finish:
                | Q(Q(cult_registry_check_ended__isnull=True) & Q(cult_registry_check_started__lte=recent_deadline))
                # After a longer deadline check NGOs which were already present in the registry:
                | Q(Q(is_in_cult_registry=True) & Q(cult_registry_check_started__lte=long_deadline))
                # After a shorter deadline check NGOs which are were still absent from the registry:
                | Q(Q(is_in_cult_registry=False) & Q(cult_registry_check_started__lte=short_deadline))
            )
            .order_by("-date_created")
            .values_list("registration_number", flat=True)[: settings.ANAF_CULT_REGISTRY_BATCH_SIZE]
        )

        result = cult_registry_check_organizations(list(registration_numbers), "sync")
        print(result)
