"""
This file contains Selenium tests, using a splinter wrapper.
"""

import os
import time

import pytest
from splinter import Browser

from redirectioneaza import app, db, User

ASSETS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')

DEV_SERVER_HOST = app.config['DEV_SERVER_HOST']
DEV_SERVER_PORT = app.config['DEV_SERVER_PORT']

APP_ADDRESS = f'http://{DEV_SERVER_HOST}:{DEV_SERVER_PORT}'

ADDRESSES = {
    'login': APP_ADDRESS + '/login',
    'logout': APP_ADDRESS + '/logout',
    'signup': APP_ADDRESS + '/cont-nou',
    'ngo-details': APP_ADDRESS + '/asociatia'
}


@pytest.fixture()
def browser():
    browser = Browser('firefox', headless=False)
    yield browser
    browser.quit()


def login_enter_data(browser, email, password):
    url = ADDRESSES['login']
    browser.visit(url)
    browser.fill('email', email)
    browser.fill('parola', password)
    button = browser.find_by_id('login-submit')
    button.click()


def signup_enter_data(browser):
    url = ADDRESSES['signup']
    browser.visit(url)
    browser.fill('nume', 'Testulescu')
    browser.fill('prenume', 'Testulovici')
    browser.fill('email', 'testulescu@example.com')
    browser.fill('parola', 'testuser')
    agree = browser.find_by_id('agree').click()
    button = browser.find_by_id('signup-submit')
    button.click()


def signup_cleanup():
    # Warning! Not having the appropriate DB environment variables defined will cause this method (and any test that's
    # using it) to fail.

    _user = User.query.filter_by(email='testulescu@example.com').first()
    if not _user:
        return
    else:
        db.session.delete(_user)
        db.session.commit()


def test_login_user_success(browser):
    login_enter_data(browser, email='user1@example.com', password='testuser')
    assert browser.is_text_present('Mai jos gasesti o lista cu toate persoanele care au completat formularul de 2%:')


def test_login_admin_success(browser):
    login_enter_data(browser, email='admin@example.com', password='admin')
    assert browser.is_text_present('Salut, Adminovici. Bine ai venit pe redirectioneaza.ro')


def test_login_user_fail(browser):
    login_enter_data(browser, email='user1@example.com', password='obviouslywrongpassword.jpg')
    assert browser.is_text_present('Se pare ca aceasta combinatie de email si parola este incorecta.')


def test_login_admin_fail(browser):
    login_enter_data(browser, email='admin@example.com', password='notoriouslywrongpassword.jpg')
    assert browser.is_text_present('Se pare ca aceasta combinatie de email si parola este incorecta.')


def test_signup_success(browser):
    signup_cleanup()
    signup_enter_data(browser)
    assert browser.is_text_present('Salut, Testulescu. Bine ai venit pe redirectioneaza.ro')
    signup_cleanup()


def test_signup_fail(browser):
    signup_cleanup()
    signup_enter_data(browser)
    logout_url = ADDRESSES['logout']
    browser.visit(logout_url)
    signup_url = ADDRESSES['signup']
    browser.visit(signup_url)
    signup_enter_data(browser)
    assert browser.is_text_present('Exista deja un cont cu aceasta adresa.')
    signup_cleanup()


def test_update_ngo_data_user_success(browser):
    login_enter_data(browser, email='user1@example.com', password='testuser')

    browser.visit(ADDRESSES['ngo-details'])

    time.sleep(2)

    browser.fill('ong-nume', 'IMPOSSIBLE 111 NEW NAME')

    browser.fill('ong-adresa', 'str. Noua 123')

    browser.fill('ong-cif', '12345678')

    browser.fill('ong-cont', 'RO1234DD45213431')

    browser.find_option_by_text("Sector 1").first.click()

    browser.find_by_id('ong-details-submit').first.click()

    errors = []

    if not browser.find_by_id('ong-nume').first.value == 'IMPOSSIBLE 111 NEW NAME':
        errors.append('NGO NAME update failed')

    assert not errors, "errors occurred:\n{}".format("\n".join(errors))


# TODO Fix this
@pytest.mark.skip('Work in progress')
def test_upload_image_user(browser):
    login_enter_data(browser, email='user1@example.com', password='testuser')

    browser.visit(ADDRESSES['ngo-details'])

    time.sleep(2)

    if browser.find_by_id('delete-ngo-logo').first:
        browser.find_by_id('delete-ngo-logo').first.click()

    browser.driver.find_element_by_id('ong-logo').send_keys(os.path.join(ASSETS_PATH, 'testimage.png'))

    browser.fill('ong-url', '123456789')

    browser.find_by_id('ong-details-submit').first.click()

    assert 'storage' in browser.find_by_id('ngo-logo')['src']


# TODO Fix this
@pytest.mark.skip('Work in progress')
def test_upload_image_admin(browser):
    login_enter_data(browser, email='admin@example.com', password='admin')

    if browser.find_by_id('delete-ngo-logo').first:
        browser.find_by_id('delete-ngo-logo').first.click()

    browser.driver.find_element_by_id('ong-logo').send_keys(os.path.join(ASSETS_PATH, 'testimage.png'))

    browser.fill('ong-url', '123456789')

    browser.find_by_id('ong-details-submit').first.click()

    assert 'storage' in browser.find_by_id('ngo-logo')['src']

# TODO Add test for changing the password

# TODO Add test for generating a pdf
