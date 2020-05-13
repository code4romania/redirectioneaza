

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

class NgoStats(Handler):
    
    def get(self):

        now = datetime.now()
        start_year = datetime(now.year, 1, 1, 0, 0)

        # get all the ngos
        all_ngos = NgoEntity.query().count()
        all_donors = Donor.query().count()

        ngos = NgoEntity.query(NgoEntity.date_created > start_year).count()
        donors = Donor.query(Donor.date_created > start_year).count()

        result = 'Rezultate pentru anul acesta: <br>'
        result += 'Onguri: {0} <br>'.format(ngos)
        result += 'Formulare: {0} <br><br><br>'.format(donors)

        result = 'Rezultate total: <br>'
        result += 'Onguri: {0} <br>'.format(all_ngos)
        result += 'Formulare: {0} <br><br><br>'.format(all_donors)

        self.response.write(result)


cron_routes = [
    r('/ngos/remove-form',    handler=NgoRemoveForms,    name="ngo-remove-form"),
    r('/ngos/stats',    handler=NgoStats,    name="ngo-stats")
]