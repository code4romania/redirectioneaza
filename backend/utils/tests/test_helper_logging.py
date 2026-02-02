import logging

from django.conf import settings
from django.test import TestCase, override_settings

from utils.helper_logging import setup_logger


class HelperLoggingTestCase(TestCase):
    @override_settings(CUSTOM_LOG_LEVEL="info")
    def test_setup_logger_sets_custom_level(self):
        logger_name = "utils.tests.helper_logging.custom_level"
        logger = setup_logger(logger_name)

        self.assertEqual(logger.level, logging.INFO)

    @override_settings(CUSTOM_LOG_LEVEL="")
    def test_setup_logger_keeps_existing_level_when_custom_level_falsy(self):
        logger_name = "utils.tests.helper_logging.default_level"
        logger = setup_logger(logger_name)

        self.assertEqual(logger.level, logging.getLevelNamesMapping().get(settings.DJANGO_LOG_LEVEL.upper()))
