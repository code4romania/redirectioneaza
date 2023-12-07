import operator


from datetime import datetime
from webapp2 import Route as r

from google.appengine.ext import ndb

from models.handlers import Handler
from models.models import NgoEntity, Donor

from logging import info, warn

class Stats(Handler):
    """Used to create different migrations on the data"""

    def get(self):
        now = datetime.now()
        start_of_year = datetime(now.year, 1, 1, 0, 0)
        donations = Donor.query(Donor.date_created > start_of_year).fetch(projection=["ngo", "has_signed"])

        ngos = {}
        signed = 0
        for d in donations:
            ngos[d.ngo.id()] = ngos.get(d.ngo.id(), 0)

            ngos[d.ngo.id()] += 1

            if d.has_signed:
                signed += 1

        sorted_x = sorted(ngos.items(), key=operator.itemgetter(1))

        res = """
        Formulare semnate: {} <br>
        Top ngos: {}
        """.format(signed, sorted_x[len(sorted_x) - 10:])

        self.response.write(res)



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
        
        string = 'Nume| Cif| Judet| Regiune de activitate| Email| Website| Adresa \n'
        for ngo in ngos:
            string += u'{0}| {1}| {2}| {3}| {4}| {5}| {6}\n'.format(ngo.name, ngo.cif, ngo.county, ngo.active_region, ngo.email, ngo.website, ngo.address)

        self.response.headers['Content-Disposition'] = 'attachment; filename="export.csv"'
        self.response.write(string)


# used to make custom exports
class CustomExport(Handler):
    def get(self):
        start_arg = self.request.get('start')
        end_arg = self.request.get('end')

        if not start_arg or not end_arg:
            self.response.write('Missing start and end from URL. Format: ?start=23-1&end=19-5')
            return

        start_arg = start_arg.split('-')
        end_arg = end_arg.split('-')
        query_start = datetime(2022, int(start_arg[1]), int(start_arg[0]), 0, 0)
        query_end = datetime(2022, int(end_arg[1]), int(end_arg[0]) + 1, 0, 0)

        # ngos = NgoEntity.query().fetch()
        donors = Donor.query(ndb.AND(Donor.date_created >= query_start, Donor.date_created < query_end)).fetch()

        info('Found {} donations'.format(len(donors)))

        string = 'Nume donator| Prenume donator| Email| A semnat| Link PDF| Nume asociatie| Email| Accepta formulare online\n'
        for donor in donors:
            ngo = donor.ngo.get()
            if ngo:
                string += u'{0}| {1}| {2}| {3}| {4}| {5}| {6}| {7}\n'.format(
                    donor.first_name, donor.last_name, donor.email, donor.has_signed, donor.pdf_url,
                    ngo.name, ngo.email, ngo.accepts_forms)
            else:
                warn('Could not find ngo for donation, ID: {}'.format(donor.key.id()))

        self.response.headers['Content-Disposition'] = 'attachment; filename="export.csv"'
        self.response.write(string)

cron_routes = [
    r('/stats',             handler=Stats),
    r('/ngos/remove-form',  handler=NgoRemoveForms,    name="ngo-remove-form"),
    r('/ngos/export',       handler=NgoExport),
    r('/export/custom',     handler=CustomExport)
]