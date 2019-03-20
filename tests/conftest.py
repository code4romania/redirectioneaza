import pytest
from splinter import Browser


@pytest.fixture()
def browser():
    browser = Browser('firefox', headless=True)
    yield browser
    browser.quit()
