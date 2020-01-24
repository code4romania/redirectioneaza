

from google.appengine.ext import ndb

from appengine_config import DEFAULT_NGO_LOGO


class BaseEntity(ndb.Model):
    """basic type of model that all other inherit from
        mainly just a wrapper for ndb.Model
    """
    pass



# to the list of counties add the whole country
class NgoEntity(BaseEntity):

    name = ndb.StringProperty(indexed=True)

    description = ndb.TextProperty()

    logo = ndb.StringProperty(indexed=True, default=DEFAULT_NGO_LOGO)
    # the background image that will go above the description, if any
    image = ndb.StringProperty(indexed=True)

    # the bank account
    account = ndb.StringProperty(indexed=True)
    cif = ndb.StringProperty(indexed=True)
    address = ndb.TextProperty()
    county = ndb.StringProperty(indexed=True)

    # the ngo's phone number
    tel = ndb.StringProperty(indexed=True)
    # the main email address used as contact
    email = ndb.StringProperty(indexed=True)
    website = ndb.StringProperty(indexed=True)
    # a list of email addresses
    other_emails = ndb.StringProperty(indexed=True, repeated=True)

    # if the ngo verified its existence
    verified = ndb.BooleanProperty(indexed=True, default=False)

    # if the ngo has a special status (eg. social ngo) they are entitled to 3.5% donation, not 2%
    special_status = ndb.BooleanProperty(indexed=True, default=False)

    # bool telling if the ngo should be shown to the public (the ngo might be banned)
    active = ndb.BooleanProperty(indexed=True, default=True)

    # url to the ngo's 2% form, that contains only the ngo's details
    form_url = ndb.StringProperty(indexed=False)

    # tags for the 
    tags = ndb.StringProperty(indexed=True, repeated=True)

    # meta data
    date_created = ndb.DateTimeProperty(indexed=True, auto_now_add=True)

    # bool telling if the ngp wants to allow the donor to upload the signed document
    allow_upload = ndb.BooleanProperty(indexed=True, default=False)


class Fundraiser(BaseEntity):
    pass

class Donor(BaseEntity):
    
    first_name = ndb.StringProperty(indexed=True)
    last_name = ndb.StringProperty(indexed=True)
    
    city = ndb.StringProperty(indexed=True)
    county = ndb.StringProperty(indexed=True)
    
    email = ndb.StringProperty(indexed=True)
    tel = ndb.StringProperty(indexed=True)

    anonymous = ndb.BooleanProperty(indexed=True, default=True)

    # type of income: wage or pension
    income = ndb.StringProperty(indexed=False, default='wage') # choices=['wage', 'pension']

    two_years = ndb.BooleanProperty(indexed=False, default=False)

    geoip = ndb.TextProperty()

    ngo = ndb.KeyProperty(indexed=True, kind="NgoEntity")

    # the pdf to be downloaded by the donor
    pdf_url = ndb.StringProperty()
    # the url of the pdf/image after it was signed and scanned
    # only if the ngo allows it
    pdf_signed_url = ndb.StringProperty()

    # meta data
    date_created = ndb.DateTimeProperty(indexed=True, auto_now_add=True)


events = ["log-in", "form-submitted"]
class Event(BaseEntity):
    what = ndb.StringProperty(indexed=True, choices=events)

    who = ndb.KeyProperty()

    when = ndb.DateTimeProperty(indexed=True, auto_now_add=True)
