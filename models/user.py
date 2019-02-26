from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import time
from core import db
 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(128),index=True)

    last_name = db.Column(db.String(128),index=True)
    
    email = db.Column(db.String(128),index=True,unique=True)

    password_hash = db.Column(db.String(128),index=True)
    
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

