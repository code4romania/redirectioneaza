
from webapp2 import Route as r

from google.appengine.ext import ndb

from models.handlers import Handler
from models.models import NgoEntity

from logging import info

class NgoRemoveForms(Handler):
    
    def get(self):
    
        # get all the ngos
        ngos = NgoEntity.query().fetch()

        info('Removing form_url from {0} ngos.'.format(len(ngos)))

        # 
        to_save = []

        # loop through them and remove the form_url
        # this will force an update on it when downloaded again
        for ngo in ngos:
            ngo.form_url = None
            to_save.append(ngo)

        ndb.put_multi(to_save)
        


cron_routes = [
    r('/ngos/remove-form',    handler=NgoRemoveForms,    name="ngo-remove-form"),
]