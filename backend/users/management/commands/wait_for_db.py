import logging
import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django command that waits for database to be available"""

    def handle(self, *args, **options):
        """Handle the command"""
        logger.info("Waiting for database...")
        current_wait_time: int = 0

        db_conn = None
        while not db_conn:
            try:
                connection.ensure_connection()
                db_conn = True
            except OperationalError:
                logger.info("Database unavailable, waiting 1 second...")
                time.sleep(1)
                current_wait_time += 1
                if current_wait_time > 30:
                    logger.warning(f"Have already been waiting for {current_wait_time} seconds.")
                elif current_wait_time > 60:
                    logger.error(f"Have already been waiting for {current_wait_time} seconds. Exiting...")
                    raise

        logger.info(self.style.SUCCESS(f"Database available after {current_wait_time} seconds!"))
