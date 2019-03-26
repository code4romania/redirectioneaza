"""
This file contains the core objects of the application: the app object, the db object and login manager.
"""

import logging
import os
import sys

from flask import Flask
from flask_login import LoginManager
from flask_mail_sendgrid import MailSendGrid
from flask_sqlalchemy import SQLAlchemy

# Main app object
app = Flask(__name__, static_folder='static', static_url_path='')

# Set current working directory to the current one
os.chdir(os.path.dirname(os.path.realpath(__file__)))

REDIR_USERNAME = os.environ.get('REDIR_USERNAME')
REDIR_PASSWORD = os.environ.get('REDIR_PASSWORD')
REDIR_DBSERVER = os.environ.get('REDIR_DBSERVER')
REDIR_DBPORT = os.environ.get('REDIR_DBPORT')
REDIR_DBCATALOG = os.environ.get('REDIR_DBCATALOG')

# Set up app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{REDIR_USERNAME}:{REDIR_PASSWORD}' \
    f'@{REDIR_DBSERVER}:{REDIR_DBPORT}/{REDIR_DBCATALOG}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('APP_SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT')

# TODO Rethink this once migrated to another object store
app.config['UPLOAD_FOLDER'] = 'storage'

# TODO: with the Environment-specific configuration, set up logging stream redirection to a database on PROD
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
app.config['MAIL_SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY')
mail = MailSendGrid(app)

# Set up flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"