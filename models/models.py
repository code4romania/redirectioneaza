from appengine_config import DEFAULT_NGO_LOGO
from datetime import datetime
from core import db
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import object_session
from sqlalchemy import select, func
from models.user import User


ngo_tags = db.Table('ngoentity_tag',\
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),\
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
        return self.name

    def __repr__(self):
        return self.name

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


    @property
    def account_attached(self):
        return object_session(self).\
            scalar(
                select([func.count(User.id)]).\
                    where(User.ngo_id==self.id)
            ) >= 1

    @property
    def number_of_donations(self):
        return object_session(self).\
            scalar(
                select([func.count(Donor.id)]).\
                    where(Donor.ngo_id==self.id)
            )


# class Fundraiser(BaseEntity):
#     pass

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
    income = db.Column(db.String(256), index=True, default='wage') # choices=['wage', 'pension']

    geoip = db.Column(db.UnicodeText())

    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo_entity.id'))
    # the pdf to be downloaded by the donor
    pdf_url = db.Column(db.String(256))
    # the url of the pdf/image after it was signed and scanned
    # only if the ngo allows it
    pdf_signed_url = db.Column(db.String(256), index=True)

    # meta data
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


# events = ["log-in", "form-submitted"]
# class Event(BaseEntity):
#     what = ndb.StringProperty(indexed=True, choices=events)

#     who = ndb.KeyProperty()

#     when = ndb.DateTimeProperty(indexed=True, auto_now_add=True)
