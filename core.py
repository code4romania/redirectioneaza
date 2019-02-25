from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from appengine_config import DEV

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:docker@localhost:5432/redir'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = b'Tq9H$_on>?/ZzVbfag5k*' if DEV else None
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"