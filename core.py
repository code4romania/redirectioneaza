from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail_sendgrid import MailSendGrid
from werkzeug.routing import BaseConverter
import os

app = Flask(__name__, static_folder='static', static_url_path='')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:docker@localhost:5432/redir'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = os.environ.get('APP_SECRET_KEY')

app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT')

db = SQLAlchemy(app)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter

app.config['MAIL_SENDGRID_API_KEY'] = os.environ.get('SENDGRID_API_KEY')
mail = MailSendGrid(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
