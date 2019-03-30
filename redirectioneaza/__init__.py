"""
This file initializes the entire package. Core parts are to be imported first, then routes.
"""
from .core import app, db, mail, login_manager
from .routes import *
