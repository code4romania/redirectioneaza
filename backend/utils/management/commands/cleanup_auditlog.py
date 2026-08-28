import logging
from datetime import timedelta

from auditlog.models import LogEntry
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Deletes expired auditlog entries"

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=settings.AUDITLOG_EXPIRY_DAYS)
        total_deleted, _per_category = LogEntry.objects.filter(timestamp__lt=cutoff_date).delete()

        logger.info("Deleted %d expired auditlog entries", total_deleted)
