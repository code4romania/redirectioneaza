# -*- coding: utf-8 -*-

from google.appengine.ext.ndb import get_multi

from models.handlers import BaseHandler
from models.models import NgoEntity

from random import sample
from logging import info

"""
Handlers used for site routing
"""
class HomePage(BaseHandler):
    template_name = 'index.html'
    def get(self):

        self.template_values["title"] = "donez si eu"

        try:
            list_keys = NgoEntity.query(NgoEntity.active == True).fetch(keys_only=True)
            list_keys = sample(list_keys, 4)
            
            ngos = get_multi(list_keys)
        except Exception, e:
            ngos = NgoEntity.query(NgoEntity.active == True).fetch(4)

        self.template_values["ngos"] = ngos
                
        # render a response
        self.render()

class ForNgoHandler(BaseHandler):
    template_name = 'for-ngos.html'
    def get(self):
        # self.abort(404)
        self.template_values["title"] = "Pentru ONG-uri"

        # render a response
        self.render()


class NgoListHandler(BaseHandler):
    template_name = 'all-ngos.html'
    def get(self):
        # self.abort(404)
        self.template_values["title"] = "Asociatii"

        ngos = NgoEntity.query(NgoEntity.active == True).fetch()
        self.template_values["ngos"] = ngos

        # render a response
        self.render()

class TermsHandler(BaseHandler):
    template_name = 'terms.html'
    def get(self):

        self.template_values["title"] = "Termeni si conditii"

        # render a response
        self.render()



class PolicyHandler(BaseHandler):
    template_name = 'policy.html'
    def get(self):

        self.template_values["title"] = "Politica de confidentialitate"

        # render a response
        self.render()
