

from datetime import datetime
from webapp2 import Route as r

from google.appengine.ext import ndb

from models.handlers import Handler
from models.models import NgoEntity, Donor

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


class NgoExport(Handler):
    def get(self):
        ngos = NgoEntity.query().fetch()
        
        string = 'Nume, Cif, Judet, Regiune de activitate, Email, Website, Adresa \n'
        for ngo in ngos:
            string += u'{0},{1}, {2}, {3}, {4}, {5}, {6}\n'.format(ngo.name, ngo.cif, ngo.county, ngo.active_region, ngo.email, ngo.website, ngo.address)

        self.response.headers['Content-Disposition'] = 'attachment; filename="export.csv"'
        self.response.write(string)

cron_routes = [
    r('/ngos/remove-form',  handler=NgoRemoveForms,    name="ngo-remove-form"),
    r('/ngos/export',       handler=NgoExport)
]