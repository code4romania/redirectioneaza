

from google.appengine.ext import ndb

class BaseEntity(ndb.Model):
    """basic type of model that all other inherit from
        mainly just a wrapper for ndb.Model
    """
    pass





class NgoEntity(BaseEntity):

    name = ndb.StringProperty(indexed=True)
    description = ndb.TextProperty()

    logo = ndb.StringProperty(indexed=True)
    # the background image that will go above the description
    image = ndb.StringProperty(indexed=True)
    
    account = ndb.StringProperty(indexed=True)
    cif = ndb.StringProperty(indexed=True)
    address = ndb.TextProperty()

    # tags for the 
    tags = ndb.StringProperty(indexed=True, repeated=True)

    # meta data
    date_created = ndb.DateTimeProperty(indexed=True, auto_now_add=True)

    # bool telling if the ngp wants to allow the donor to upload the signed document
    allow_upload = ndb.BooleanProperty(indexed=True)


class NgoAdmin(BaseEntity):
    """the admin who controls an ngo"""

    name = ndb.StringProperty(indexed=True)
    email = ndb.StringProperty(indexed=True)

    password = ndb.StringProperty(indexed=True)



class Fundraiser(BaseEntity):
    pass

class Donor(BaseEntity):
    
    first_name = ndb.StringProperty(indexed=True)
    last_name = ndb.StringProperty(indexed=True)
    
    city = ndb.StringProperty(indexed=True)
    county = ndb.StringProperty(indexed=True)
    
    email = ndb.StringProperty(indexed=True)
    tel = ndb.StringProperty()

    geoip = ndb.TextProperty()

    ngo = ndb.KeyProperty(kind="NgoEntity")

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
