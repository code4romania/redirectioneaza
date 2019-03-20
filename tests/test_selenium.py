import pytest
from splinter import Browser


@pytest.fixture()
def browser():
    browser = Browser('firefox', headless=True)
    yield browser
    browser.quit()


@pytest.mark.skip("Here for future reference purposes")
def test_login(browser):
    url = 'http://localhost:5000/login'
    browser.visit(url)
    browser.fill('email', 'user1@example.com')
    browser.fill('parola', 'testuser')
    button = browser.find_by_id('login-submit')
    button.click()
    assert browser.is_text_present('Mai jos gasesti o lista cu toate persoanele care au completat formularul de 2%:')
