
import time
from core import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# from google.appengine.ext import ndb
# from webapp2_extras.appengine.auth import models
# from webapp2_extras import security
 
# from models import BaseEntity
 
 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # def set_password(self, raw_password):
    #     """Sets the password for the current user
 
    #     :param raw_password:
    #         The raw password which will be hashed and stored
    #     """
    #     self.password = security.generate_password_hash(raw_password, length=12)
 
    # @classmethod
    # def get_by_auth_token(cls, user_id, token, subject='auth'):
    #     """Returns a user object based on a user ID and token.
 
    #     :param user_id:
    #         The user_id of the requesting user.
    #     :param token:
    #         The token string to be verified.
    #     :returns:
    #         A tuple ``(User, timestamp)``, with a user object and
    #         the token timestamp, or ``(None, None)`` if both were not found.
    #     """
    #     token_key = cls.token_model.get_key(user_id, subject, token)
    #     user_key = ndb.Key(cls, user_id)
    #     # Use get_multi() to save a RPC call.
    #     valid_token, user = ndb.get_multi([token_key, user_key])
    #     if valid_token and user:
    #         timestamp = int(time.mktime(valid_token.created.timetuple()))
    #         return user, timestamp
 
    #     return None, None

    first_name = db.Column(db.String(128),index=True)
    last_name = db.Column(db.String(128),index=True)
    
    email = db.Column(db.String(128),index=True)
    password = db.Column(db.String(128),index=True)
    
    ngo = db.Column(db.Integer, db.ForeignKey('ngo_entity.id'))

    verified = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def password(self):
        """
        Raises an attribute error if password field is trying to be modified
        :return:
        """
        raise AttributeError('password: write-only field')

    @password.setter
    def password(self, password):
        """
        Sets the password
        :param password:
        :return:
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks password hash
        :param password:
        :return:
        """
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_email(email):
        """
        Returns user by username.
        :param username: username to be retrieved
        :return: User
        """
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return "<User '{}'>".format(self.email)

