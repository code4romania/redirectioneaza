from appengine_config import DEFAULT_NGO_LOGO
from datetime import datetime
from core import db

# to the list of counties add the whole country
class NgoEntity(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    
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
    # tags = db.Column(db.String(256), index=True)

    # meta data
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # bool telling if the ngp wants to allow the donor to upload the signed document
    allow_upload = db.Column(db.Boolean, default=False)


# class Fundraiser(BaseEntity):
#     pass

# class Donor(BaseEntity):
    
#     first_name = ndb.StringProperty(indexed=True)
#     last_name = ndb.StringProperty(indexed=True)
    
#     city = ndb.StringProperty(indexed=True)
#     county = ndb.StringProperty(indexed=True)
    
#     email = ndb.StringProperty(indexed=True)
#     tel = ndb.StringProperty(indexed=True)

#     anonymous = ndb.BooleanProperty(indexed=True, default=True)

#     # type of income: wage or pension
#     income = ndb.StringProperty(indexed=False, default='wage') # choices=['wage', 'pension']

#     geoip = ndb.TextProperty()

#     ngo = ndb.KeyProperty(indexed=True, kind="NgoEntity")

#     # the pdf to be downloaded by the donor
#     pdf_url = ndb.StringProperty()
#     # the url of the pdf/image after it was signed and scanned
#     # only if the ngo allows it
#     pdf_signed_url = ndb.StringProperty()

#     # meta data
#     date_created = ndb.DateTimeProperty(indexed=True, auto_now_add=True)


# events = ["log-in", "form-submitted"]
# class Event(BaseEntity):
#     what = ndb.StringProperty(indexed=True, choices=events)

#     who = ndb.KeyProperty()

#     when = ndb.DateTimeProperty(indexed=True, auto_now_add=True)
