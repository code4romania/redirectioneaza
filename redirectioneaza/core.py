"""
This file contains the core objects of the application: the app object, the db object and login manager.
"""

import logging
import sys
from os import chdir, path

from flask import Flask
from flask_login import LoginManager
from flask_mail_sendgrid import MailSendGrid
from flask_sqlalchemy import SQLAlchemy

from redirectioneaza.config import *
from redirectioneaza.contact_data import CONTACT_FORM_URL

# Main app object
app = Flask(__name__, static_folder='static', static_url_path='')

app.jinja_env.add_extension('jinja2.ext.autoescape')
app.jinja_env.add_extension('jinja2.ext.i18n')

template_settings = {
    "bower_components": DEV_DEPENDECIES_LOCATION,
    "DEV": DEV,
    "PRODUCTION": PRODUCTION,
    "title": TITLE,
    "contact_url": CONTACT_FORM_URL,
    "language": "ro",
    "base_url": "/",
    "captcha_public_key": CAPTCHA_PUBLIC_KEY,
    "errors": None
}

app.jinja_env.globals = {**app.jinja_env.globals, **template_settings}

app.config.from_object('redirectioneaza.config')
app.config.from_object(CONFIG_BY_NAME[ENVIRONMENT])

# Set current working directory to the current one
chdir(path.dirname(path.realpath(__file__)))

# TODO: Refactor and/or Move logging logic to another file
# Handle all logging streams
out_hdlr = logging.StreamHandler(sys.stdout)
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
out_hdlr.setFormatter(fmt)
out_hdlr.setLevel(logging.INFO)
# append to the global logger.
logging.getLogger().addHandler(out_hdlr)
logging.getLogger().setLevel(logging.INFO)
# removing the handler and
# re-adding propagation ensures that
# the root handler gets the messages again.
app.logger.handlers = []
app.logger.propagate = True

# Set up database object
db = SQLAlchemy(app)

# Set up flask-mail-sendgrid
mail = MailSendGrid(app)

# Set up flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"