# -*- coding: utf-8 -*-
"""
This file contains the unit test for the applications. All of the use the client fixtures so the app doesn't need to be
up for the tests to be run. Tests are auto-detected by pytest.
"""

import os
import tempfile

import pytest

from redirectioneaza import app


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def test_index(client):
    rv = client.get('/')

    assert "Redirecționează 2% din impozit" in rv.data.decode('utf-8')


def test_ong(client):
    rv = client.get('/ong')

    assert "Reprezinti un ONG si doresti sa-ti cresti organizatia?" in rv.data.decode('utf-8')


def test_ong_legacy(client):
    rv = client.get('/pentru-ong-uri')

    assert "Reprezinti un ONG si doresti sa-ti cresti organizatia?" in rv.data.decode('utf-8')


def test_ngo_list(client):
    rv = client.get('/asociatii')

    assert "Asociații pentru care poți redirecționa 2%" in rv.data.decode('utf-8')


def test_terms(client):
    rv = client.get('/termeni')

    assert "Termeni si conditii de utilizare" in rv.data.decode('utf-8')


def test_note(client):
    rv = client.get('/nota-de-informare')

    assert "Nota de informare" in rv.data.decode('utf-8')


def test_policy(client):
    rv = client.get('/politica')

    assert "website foloseste cookie-uri pentru a furniza vizitatorilor o experienta" in rv.data.decode('utf-8')


def test_about(client):
    rv = client.get('/despre')

    assert "Despre Redirectioneaza.ro" in rv.data.decode('utf-8')


def test_signup_get(client):
    rv = client.get('/cont-nou')

    assert "Cont nou" in rv.data.decode('utf-8')


# TODO Change recaptcha validation to be overridden while on DEV. This will allow us to test all methods as below.
@pytest.mark.skip("Need to ignore recaptcha for unit testing")
def test_signup_post(client):
    rv = client.post('/cont-nou', data=dict(nume='Jio', prenume='Gogo', email='jiogogo@example.com', parola='1234'))

    x = rv.data.decode('utf-8')
    assert "Se pare ca a fost o problema cu verificarea reCAPTCHA." in rv.data.decode('utf-8')
