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

        self.template_values["title"] = "redirectioneaza.ro"

        self.template_values['limit'] = DONATION_LIMIT
        self.template_values["DEFAULT_NGO_LOGO"] = DEFAULT_NGO_LOGO

        # if we are on the ikea subdomain, load the special page
        if self.is_ikea_subdomain:
            ikea_ngos = [
                'asociatia-aura-ion',
                'asociatia-activity',
                'asociatia-ana-si-copiii',
                'asociatia-caritas-bucuresti',
                'asociatia-casa-ioana',
                'asociatia-ecoteca',
                'asociatia-help-autism',
                'asociatia-magicamp',
                'asociatia-traieste-cu-bucurie',
                'asociatia-unu-si-unu',
                'code-for-romania',
                'filiala-bucureti-a-asociaiei-terra-dacica-aeterna',
                'freemiorita',
                'fundatia-hospice-casa-sperantei',
                'fundatia-motivation-romania',
                'fundatia-cmu-regina-maria',
                'liliecii-din-mediul-urban',
                'organizatia-umanitara-concordia',
                'padureacopiilor',
                'scoala-de-valori',
                'societatea-nationala-de-cruce-rosie-din-romania-filiala-sector-6-bucuresti',
                'teach-for-romania',
                'viitorplus',
                'world-vision-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in ikea_ngos])
            self.template_values['company_name'] = 'IKEA'

        elif self.is_lidl_subdomain:
            lidl_ngos = [
                'asociatia-banca-locala-pentru-alimente-roman',
                'banca-pentru-alimente-oradea',
                'bancadealimentecluj',
                'asociatia-centrul-step-by-step-pentru-educatie-si-dezvoltare-profesionala',
                'asociatia-mai-mult-verde',
                'asociatia-pentru-protectia-animalelor-cezar',
                'asociatia-pentru-protectia-animalelor-kola-kariola',
                'asociatia-pentru-valori-in-educatie',
                'asociatia-robi',
                'banca-pentru-colectarea-si-distributia-alimentelor',
                'banca-regionala-pentru-alimente-brasov',
                'code-for-romania',
                'free-amely-2007',
                'fundatianoiorizonturi',
                'fundatia-comunitara-iasi',
                'fundatia-comunitara-bucuresti',
                'fundatia-motivation-romania',
                'fundatia-pentru-smurd',
                'sor',
                'httpwwwsalvaticopiiirodoilasuta',
                'teach-for-romania',
                'world-vision-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in lidl_ngos])
            self.template_values['company_name'] = 'LIDL'

        elif self.is_jysk_subdomain:
            jysk_ngos = [
                'asociatia-anais',
                'asociatia-autism-europa-centrul-de-resurse-si-referinta-in-autism-micul-print',
                'asociatia-ecoassist-iniiativa-plantam-fapte-bune-in-romania',
                'asociatia-magicamp',
                'asociatia-necuvinte',
                'asociatia-salvatorilor-montani-victoria',
                'code-for-romania',
                'comitetul-national-paralimpic',
                'inimacopiilor',
                'hopeandhomesromania',
                'policy-center-for-roma-and-minorities'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in jysk_ngos])
            self.template_values['company_name'] = 'JYSK'

        elif self.is_avon_subdomain:
            avon_ngos = [
                'asociatia-anais',
                'asociatia-mame',
                'asociatia-touched-romania',
                'caravanacumedici',
                'code-for-romania',
                'ffff',
                'navimed-navigatori-medicali'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in avon_ngos])
            self.template_values['company_name'] = 'AVON'

        elif self.is_carturesti_subdomain:
            carturesti_ngos = [
                'ajungemmari',
                'asociatia-magicamp',
                'code-for-romania',
                'fundatiacarturesti',
                'teach-for-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in carturesti_ngos])
            self.template_values['company_name'] = 'CARTURESTI'

        elif self.is_cez_subdomain:
            cez_ngos = [
                'asociatia-habitat-for-humanity-romania',
                'asociatia-little-people-romania',
                'fundatia-sf-dimitrie',
                'fundatianoiorizonturi',
                'niciodatasingur',
                'sonoro',
                'the-social-incubator',
                'world-vision-romania',
                'code-for-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in cez_ngos])
            self.template_values['company_name'] = 'CEZ'

        elif self.is_ing_subdomain:
            ing_ngos = [
               'asociatiapentrudezvoltareurbana',
               'asociatia-ana-si-copiii',
               'asociatia-club-lions-diamond',
               'asociatia-daruieste-aripi',
               'asociatia-ropot',
               'asociatia-mame',
               'caravanacumedici',
               'carusel',
               'code-for-romania',
               'fundatia-entreprenation',
               'fundatia-comunitara-bucuresti',
               'fundatia-hospice-casa-sperantei',
               'inimacopiilor',
               'un-copil-o-speranta',
               'viitorplus'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in ing_ngos])
            self.template_values['company_name'] = 'ING'

        elif self.is_patria_subdomain:
            patria_ngos = [
                'asociatia-ana-si-copiii',
                'asociatia-ateliere-fara-frontiere',
                'asociatia-crestem-romania-impreuna',
                'asociatia-kinetobebe',
                'asociatia-administratorilor-de-piete-din-romania',
                'asociatia-pedia-pentru-sprijinirea-copiilor-cu-deficiente-neuropsihomotorii',
                'atca-asociatia-de-terapie-comportamentala-aplicata',
                'code-for-romania',
                'the-social-incubator',
                'viitorplus',
                'world-vision-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in patria_ngos])
            self.template_values['company_name'] = 'PATRIA BANK'

        elif self.is_continental_subdomain:
            continental_ngos = [
                'asociatia-pro-palatul-copiilor-sibiu',
                'ajungemmari',
                'animallife',
                'aleg',
                'ama-zambet-de-copil',
                'asociatia-casa-share',
                'asociatia-crestina-for-help',
                'asociatia-iti-arat-ca-pot',
                'asociatia-little-people-romania',
                'asociatia-magicamp',
                'asociatia-pro-palatul-copiilor-sibiu',
                'asociatia-stergem-o-lacrima',
                'asociatia-umanitara-dare-to-care',
                'baby-care-sibiu',
                'capitalcultural',
                'cu-verdele-n-sus',
                'fundatia-pentru-smurd',
                'fundatia-pentru-voi',
                'fundatia-united-way-romania',
                'mainiunite',
                'politehnica',
                'recorder',
                'un-copil-o-speranta',
                'code-for-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in continental_ngos])
            self.template_values['company_name'] = 'CONTINENTAL'

        elif self.is_smartbill_subdomain:
            smartbill_ngos = [
                'animallife',
                'asociatiasusinima',
                'asociatia-de-poveste',
                'asociatia-magicamp',
                'asociatia-little-people-romania',
                'baby-care-sibiu',
                'cu-verdele-n-sus',
                'fundatia-comunitara-sibiu',
                'fundatia-polisano',
                'la-primul-bebe'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in smartbill_ngos])
            self.template_values['company_name'] = 'SMARTBILL'

        elif self.is_nestle_subdomain:
            nesle_ngos = [
                'asociatia-valentina-romania',
                'banca-pentru-colectarea-si-distributia-alimentelor',
                'clubul-cainilor-utilitari-echipa-de-cautare-si-salvare-search-and-rescue',
                'sos-satele-copiilor-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in nesle_ngos])
            self.template_values['company_name'] = 'NESTLE'

        elif self.is_digi_subdomain:
            digi_ngos = [
                'asociatia-ateliere-fara-frontiere',
                'angels-down-friends',
                'asociatia-orizont-de-inger',
                'casiopeea',
                'code-for-romania',
                'hopeandhomesromania',
                'httpwwwsalvaticopiiirodoilasuta',
                'sos-satele-copiilor-romania',
                'world-vision-romania',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in digi_ngos])
            self.template_values['company_name'] = 'DIGI'

        elif self.is_raiffeisen_subdomain:
            raiffeisen_ngos = [
                'aspen-romania',
                'asociatia-coolturala-noua-ne-pasa',
                'asociatia-dream-project',
                'asociatia-civica',
                'asociatia-green-revolution',
                'asociatia-hercules',
                'asociatia-romana-de-dezbateri-oratorie-si-retorica-ardor',
                'asociatia-studentilor-francofoni-din-iasi',
                'code-for-romania',
                'fundatia-cmu-regina-maria',
                'fanzin',
                'fundatia-alma-mater-napocensis',
                'fundatia-cartea-calatoare',
                'fundatia-dezvoltarea-popoarelor-filiala-cluj',
                'fundatia-hategan',
                'fundatia-leaders',
                'fundatia-light-into-europe',
                'fundatia-principesa-margareta-a-romaniei',
                'fundatia-united-way-romania',
                'junior-achievement-romania',
                'yuppicamp',
                'teach-for-romania',
                'sonoro',
                'tasuleasa-social',
                # TODO: add the following NGOs when available:
                # OvidiuRo
                # Asociatia pentru Relatii Comunitare(ARC)
                # Asociatia Clubul Sportiv Bucharest Running Club
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in raiffeisen_ngos])
            self.template_values['company_name'] = 'Raiffeisen Bank'

        else:
            try:
                list_keys = NgoEntity.query(NgoEntity.active == True).fetch(keys_only=True)
                list_keys = sample(list_keys, 4)

                ngos = get_multi(list_keys)
            except Exception, e:
                info(e)
                ngos = NgoEntity.query(NgoEntity.active == True).fetch(4)

        # filter out all the keys that we couldn't find
        ngos = [n for n in ngos if n]

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
