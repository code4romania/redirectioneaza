"""
This file contains the Models that the application uses.
"""

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.security import check_password_hash, generate_password_hash

from redirectioneaza import db
from redirectioneaza.config import DEFAULT_NGO_LOGO

ngo_tags = db.Table('ngo_entity_tag', db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                    db.Column('ngoentity_id', db.Integer, db.ForeignKey('ngo_entity.id')))


class Tag(db.Model):
    """
    Defines the Tag object.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True, index=True)

    @staticmethod
    def get_or_create(name):
        """
        Gets or creates a tag with a given name.
        :param name: string, name of the tag to be found or created if it doesn't exist.
        :return:  Tag
        """
        try:
            return Tag.query.filter_by(name=name).one()
        except NoResultFound:
            return Tag(name=name)

    @staticmethod
    def all():
        """
        Returns all the tags.
        :return: Tag(s)
        """
        return Tag.query.all()

    def __str__(self):
        return "<Tag '{}'>".format(self.name)

    def __repr__(self):
        return "<Tag '{}'>".format(self.name)


# to the list of counties add the whole country

class NgoEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True)

    name = db.Column(db.String(100))

    description = db.Column(db.UnicodeText())

    logo = db.Column(db.String(256), index=True, default=DEFAULT_NGO_LOGO)
    # the background image that will go above the description, if any
    image = db.Column(db.String(256), index=True)

    # the bank account
    account = db.Column(db.String(256), index=True)
    cif = db.Column(db.String(256), index=True)
    address = db.Column(db.UnicodeText())
    county = db.Column(db.String(256), index=True)

    # the ngo's phone number
    tel = db.Column(db.String(256), index=True)
    # the main email address used as contact
    email = db.Column(db.String(256), index=True)
    website = db.Column(db.String(256), index=True)
    # a list of email addresses
    other_emails = db.Column(db.String(256), index=True)

    # if the ngo verified its existence
    verified = db.Column(db.Boolean, default=False)

    # if the ngo has a special status (eg. social ngo) they are entitled to 3.5% donation, not 2%
    special_status = db.Column(db.Boolean, default=False)

    # bool telling if the ngo should be shown to the public (the ngo might be banned)
    active = db.Column(db.Boolean, default=True)

    # url to the ngo's 2% form, that contains only the ngo's details
    form_url = db.Column(db.String(256), index=True)

    # # tags for the
    tags = db.relationship('Tag', secondary=ngo_tags)

    # meta data
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # bool telling if the ngp wants to allow the donor to upload the signed document
    allow_upload = db.Column(db.Boolean, default=False)

    users = db.relationship('User', backref='ngo')
    donors = db.relationship('Donor', backref='ngo')

    @hybrid_property
    def num_donors(self):
        try:
            return Donor.query.filter(Donor.ngo_id == self.id).count()
        except OperationalError:
            return None

    @property
    def account_attached(self):
        return object_session(self).scalar(select([func.count(User.id)]).where(User.ngo_id == self.id)) >= 1

    @property
    def number_of_donations(self):
        return object_session(self).scalar(select([func.count(Donor.id)]).where(Donor.ngo_id == self.id))

    def __str__(self):
        return "<NGO '{}'>".format(self.name)

    def __repr__(self):
        return "<NGO '{}'>".format(self.name)


class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256), index=True)
    last_name = db.Column(db.String(256), index=True)

    city = db.Column(db.String(256), index=True)
    county = db.Column(db.String(256), index=True)

    email = db.Column(db.String(120), unique=True, index=True)
    tel = db.Column(db.String(256), index=True)

    anonymous = db.Column(db.Boolean, default=True)

    # type of income: wage or pension
    income = db.Column(db.String(256), index=True, default='wage')  # choices=['wage', 'pension']

    geoip = db.Column(db.UnicodeText())

    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo_entity.id'))
    # the pdf to be downloaded by the donor
    pdf_url = db.Column(db.String(256))
    # the url of the pdf/image after it was signed and scanned
    # only if the ngo allows it
    pdf_signed_url = db.Column(db.String(256), index=True)

    # meta data
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __str__(self):
        return "<Donor '{}'>".format(self.first_name + ' ' + self.last_name)

    def __repr__(self):
        return "<Donor '{}'>".format(self.first_name + ' ' + self.last_name)


# TODO Investigate where this was used
# events = ["log-in", "form-submitted"]
# class Event(BaseEntity):
#     what = ndb.StringProperty(indexed=True, choices=events)

#     who = ndb.KeyProperty()

#     when = ndb.DateTimeProperty(indexed=True, auto_now_add=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(128), index=True)

    last_name = db.Column(db.String(128), index=True)

    email = db.Column(db.String(128), index=True, unique=True)

    password_hash = db.Column(db.String(128), index=True)

    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo_entity.id'))

    verified = db.Column(db.Boolean, nullable=False, default=False)

    admin = db.Column(db.Boolean, nullable=False, default=False)

    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def is_admin(self):
        return self.admin

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

    def __str__(self):
        return "<User '{}'>".format(self.email)

    def __repr__(self):
        return "<User '{}'>".format(self.email)
