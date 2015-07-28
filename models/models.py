

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
    tel = ndb.StringProperty(indexed=True)

    geoip = ndb.TextProperty()

    # meta data
    date_created = ndb.DateTimeProperty(indexed=True, auto_now_add=True)