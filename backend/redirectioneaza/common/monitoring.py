import logging
from typing import List

from django.conf import settings
from django_q.status import Stat
from sentry_sdk import capture_message

logger = logging.getLogger(__name__)


def check_queue_status():
    try:
        cluster_status: List[Stat] = Stat.get_all()

        if len(cluster_status) == 0:
            error_message = "No clusters found. Please check the status of the server."

            logger.warning(error_message)

            if settings.ENABLE_SENTRY:
                capture_message(error_message, level="error")
        else:
            for stat in cluster_status:
                if stat.task_q_size > 50:
                    error_message = "Too many tasks in queue. Please check the status of the server."
                    logger.warning(error_message)

                    if settings.ENABLE_SENTRY:
                        capture_message(error_message, level="error")
    except Exception as e:
        logger.error(f"Error checking task count: {e}")
