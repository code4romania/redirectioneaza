"""
This file contains test fixtures to be used by Selenium tests
"""

import pytest
from splinter import Browser


@pytest.fixture()
def browser():
    """
    Pytest fixture to be used by Selenium tests.
    :return: yields Browser
    """
    browser = Browser('firefox', headless=True)
    yield browser
    browser.quit()
