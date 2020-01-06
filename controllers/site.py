# -*- coding: utf-8 -*-

from google.appengine.ext.ndb import get_multi, Key

from appengine_config import DEFAULT_NGO_LOGO, DONATION_LIMIT
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

        self.template_values["title"] = "redirectioneaza 2%"

        self.template_values['limit'] = DONATION_LIMIT
        self.template_values["DEFAULT_NGO_LOGO"] = DEFAULT_NGO_LOGO

        # if we are on the ikea subdomain, load the special page
        if self.is_ikea_subdomain:
            ikea_ngos = [
                'asociatia-aura-ion',
                'asociatia-caritas-bucuresti',
                'asociatia-casa-ioana',
                'code-for-romania',
                'organizatia-umanitara-concordia',
                'societatea-nationala-de-cruce-rosie-din-romania-filiala-sector-6-bucuresti',
                'asociatia-ecoteca',
                'freemiorita',
                'asociatia-help-autism',
                'asociatia-magicamp',
                'fundatia-motivation-romania',
                'padureacopiilor',
                'scoala-de-valori',
                'teach-for-romania',
                'filiala-bucureti-a-asociaiei-terra-dacica-aeterna',
                'asociatia-unu-si-unu',
                'viitorplus',
                'world-vision-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in ikea_ngos])
            # filter out all they keys that we couldn't find
            ngos = [n for n in ngos if n]

        else:
            try:
                list_keys = NgoEntity.query(NgoEntity.active == True).fetch(keys_only=True)
                list_keys = sample(list_keys, 4)
                
                ngos = get_multi(list_keys)
            except Exception, e:
                info(e)
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
        self.template_values["DEFAULT_NGO_LOGO"] = DEFAULT_NGO_LOGO

        # render a response
        self.render()

class TermsHandler(BaseHandler):
    template_name = 'terms.html'
    def get(self):

        self.template_values["title"] = "Termeni si conditii"

        # render a response
        self.render()

class NoteHandler(BaseHandler):
    template_name = 'note.html'
    def get(self):

        self.template_values["title"] = "Nota de informare"

        # render a response
        self.render()

class AboutHandler(BaseHandler):
    template_name = 'despre.html'
    def get(self):

        self.template_values["title"] = "Despre Redirectioneaza.ro"

        # render a response
        self.render()

class PolicyHandler(BaseHandler):
    template_name = 'policy.html'
    def get(self):

        self.template_values["title"] = "Politica de confidentialitate"

        # render a response
        self.render()

def NotFoundPage(request, response, exception):
    """handles the 404 page
        we can't use BaseHandler for this page. 
        webapp2 only accepts a simple function like this one
    """
    
    # create a mock handler so we can user templates
    handler = BaseHandler(request, response)

    response.set_status(404)

    handler.render('404.html')

def InternalErrorPage(request, response, exception):
    """handles the 500 page. same as the 404 page
    """
    
    # create a mock handler so we can user templates
    handler = BaseHandler(request, response)

    from logging import critical

    critical(exception, exc_info=1)

    response.set_status(500)

    handler.render('500.html')
