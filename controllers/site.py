# -*- coding: utf-8 -*-
from datetime import datetime

from google.appengine.ext.ndb import get_multi, Key

from appengine_config import DEFAULT_NGO_LOGO, DONATION_LIMIT
from models.handlers import BaseHandler
from models.models import NgoEntity, Donor

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
                'asociatia-caritas-bucuresti',
                'asociatia-casa-ioana',
                'asociatia-climb-again',
                'asociatia-activity',
                'asociatia-help-autism',
                'asociatia-magic',
                'padureacopiilor',
                'asociatia-traieste-cu-bucurie',
                'asociatia-unu-si-unu',
                'code-for-romania',
                'societatea-nationala-de-cruce-rosie-din-romania-filiala-sector-6-bucuresti',
                'freemiorita',
                'fundatia-motivation-romania',
                'fundatia-cmu-regina-maria',
                'world-vision-romania',
                'organizatia-umanitara-concordia',
                'liliecii-din-mediul-urban',
                'teach-for-romania',
                'viitorplus',
                'asociatia-de-ajutor-amurtel',
                'atca-asociatia-de-terapie-comportamentala-aplicata',
                'asociatia-blondie',
                'asociatia-casa-buna',
                'gritty',
                'asociatia-habitat-for-humanity-romania',
                'asociatia-hai-cu-bicla',
                'hopeandhomesromania',
                'asociatia-kogayon',
                'ajungemmari',
                'ovidiuro',
                'asociatia-parcul-natural-vacaresti',
                'roma-education-fund-romania',
                'httpwwwsalvaticopiiirodoilasuta',
                'sos-satele-copiilor-romania',
                'zi-de-bine',
                'bikers-for-humanity',
                'fundatia-usa-deschisa',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in ikea_ngos])
            self.template_values['company_name'] = 'IKEA'

        elif self.is_lidl_subdomain:
            lidl_ngos = [
                'asociatia-banca-locala-pentru-alimente-roman',
                'banca-pentru-alimente-oradea',
                'asociatia-centrul-step-by-step-pentru-educatie-si-dezvoltare-profesionala',
                'asociatia-pentru-protectia-animalelor-cezar',
                'asociatia-mai-mult-verde',
                'asociatia-pentru-protectia-animalelor-cezar',
                'asociatia-pentru-protectia-animalelor-kola-kariola',
                'asociatia-robi',
                'asociatia-pentru-valori-in-educatie',
                'wwf',
                'banca-pentru-colectarea-si-distributia-alimentelor',
                'banca-regionala-pentru-alimente-brasov',
                'bancadealimentecluj',
                'code-for-romania',
                'fundatia-comunitara-bucuresti',
                'fundatia-comunitara-iasi',
                'fundatia-motivation-romania',
                'fundatianoiorizonturi',
                'world-vision-romania',
                'httpwwwsalvaticopiiirodoilasuta',
                'sor',
                'teach-for-romania',
                'ffcr',
                'fundatia-leaders',
                'the-institute',
                'asociatia-banca-regionala-pentru-alimente-timisoara',
                'banca-regionala-pentru-alimente-constanta',
                'fundatiacomunitaracluj',
                'fco',
                'fundatia-comunitara-brasov',
                'fundatia-comunitara-galati',
                'zi-de-bine',
                'media-dor',
                'ambasada-sustenabilitatii-in-romania',
                'fundatia-motivation-romania',
                'asociatia-little-people-romania',
                'fundatia-hospice-casa-sperantei'
                'clubul-cainilor-utilitari',
                'free-amely-2007',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in lidl_ngos])
            self.template_values['company_name'] = 'LIDL'

        elif self.is_jysk_subdomain:
            jysk_ngos = [
                'asociatia-anais',
                'asociatia-autism-europa-centrul-de-resurse-si-referinta-in-autism-micul-print',
                'asociatia-casa-buna',
                'asociatia-ecoassist-iniiativa-plantam-fapte-bune-in-romania',
                'asociatia-kinetobebe',
                'asociatia-magic',
                'asociatia-salvatorilor-montani-victoria',
                'code-for-romania',
                'comitetul-national-paralimpic',
                'hopeandhomesromania',
                'wwf',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in jysk_ngos])
            self.template_values['company_name'] = 'JYSK'

        elif self.is_avon_subdomain:
            avon_ngos = [
                'asociatia-anais',
                'caravanacumedici',
                'asociatia-mame',
                'asociatia-touched-romania',
                'code-for-romania',
                'ffff',
                'navimed-navigatori-medicali',
                'zi-de-bine',
                'asociatia-necuvinte',
                'asociatia-pentru-preventia-si-lupta-impotriva-cancerului-amazonia',
                'fundatia-cmu-regina-maria',
                'fundatia-hospice-casa-sperantei',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in avon_ngos])
            self.template_values['company_name'] = 'AVON'

        elif self.is_carturesti_subdomain:
            carturesti_ngos = [
                'ajungemmari',
                'asociatia-magic',
                'code-for-romania',
                'fundatiacarturesti',
                'teach-for-romania',
                'asociatia-pirita-children-copiii-din-pirita',
                'asociatia-casa-buna',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in carturesti_ngos])
            self.template_values['company_name'] = 'CARTURESTI'

        elif self.is_cez_subdomain:
            cez_ngos = [
                'asociatia-little-people-romania',
                'sonoro',
                'the-social-incubator',
                'code-for-romania',
                'fundatianoiorizonturi',
                'fundatia-sf-dimitrie',
                'world-vision-romania',
                'asociatia-habitat-for-humanity-romania',
                'niciodatasingur',
                'asociatia-vatra-cu-idei',
                'fundatia-progress',
                'yesromania',
                'fundatia-alex-tache',
                'fundatia-principesa-margareta-a-romaniei',
                'httpwwwsalvaticopiiirodoilasuta',
                'asociatia-roi',
                'asociatia-vasiliada',
                'crucea-rosie-filiala-teleorman',
                'filiala-de-cruce-rosie-constanta',
                'filiala-de-cruce-rosie-olt',
                'crucea-rosie-romana-filiala-valcea',
                'lets-do-it-romania'
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in cez_ngos])
            self.template_values['company_name'] = 'CEZ'

        elif self.is_ing_subdomain:
            ing_ngos = [
                'asociatia-ana-si-copiii',
                'asociatia-daruieste-aripi',
                'asociatia-educatie-pentru-viata-reala',
                'asociatia-pavel',
                'asociatia-ropot',
                'asociatia-mame',
                'carusel',
                'code-for-romania',
                'fundatia-entreprenation',
                'fundatia-comunitara-bucuresti',
                'fundatia-inima-de-copil',
                'inimacopiilor',
                'viitorplus',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in ing_ngos])
            self.template_values['company_name'] = 'ING'

        elif self.is_patria_subdomain:
            patria_ngos = [
                'asociatia-administratorilor-de-piete-din-romania',
                'asociatia-ana-si-copiii',
                'asociatia-ateliere-fara-frontiere',
                'asociatia-crestem-romania-impreuna',
                'asociatia-inspiraction',
                'asociatia-kinetobebe',
                'asociatia-micile-bucurii',
                'asociatia-pedia-pentru-sprijinirea-copiilor-cu-deficiente-neuropsihomotorii',
                'atca-asociatia-de-terapie-comportamentala-aplicata',
                'code-for-romania',
                'daruieste-viata',
                'fundatia-patria-credit',
                'the-social-incubator',
                'world-vision-romania',
                'viitorplus',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in patria_ngos])
            self.template_values['company_name'] = 'PATRIA BANK'

        elif self.is_continental_subdomain:
            continental_ngos = [
                'ajungemmari',
                'ama-zambet-de-copil',
                'capitalcultural',
                'asociatia-casa-share',
                'asociatia-crestina-for-help',
                'asociatia-iti-arat-ca-pot',
                'asociatia-little-people-romania',
                'asociatia-magic',
                'asociatia-oncohelp',
                'mainiunite',
                'aleg',
                'animallife',
                'asociatia-pro-palatul-copiilor-sibiu',
                'recorder',
                'asociatia-stergem-o-lacrima',
                'asociatia-umanitara-dare-to-care',
                'baby-care-sibiu',
                'code-for-romania',
                'cu-verdele-n-sus',
                'fundatia-pentru-voi',
                'fundatia-pentru-smurd',
                'fundatia-united-way-romania',
                'politehnica',
                'un-copil-o-speranta',
                'fundatia-serviciilor-sociale-bethany',
                'fundatia-comunitara-iasi',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in continental_ngos])
            self.template_values['company_name'] = 'CONTINENTAL'

        elif self.is_smartbill_subdomain:
            smartbill_ngos = [
                'asociatia-de-poveste',
                'la-primul-bebe',
                'asociatia-little-people-romania',
                'asociatia-magic',
                'animallife',
                'asociatiasusinima',
                'baby-care-sibiu',
                'cu-verdele-n-sus',
                'fundatia-comunitara-sibiu',
                'fundatia-polisano',
                'asociatialuthelo',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in smartbill_ngos])
            self.template_values['company_name'] = 'SMARTBILL'

        elif self.is_nestle_subdomain:
            nesle_ngos = [
                'calator-prin-romania',
                'acasainbanat',
                'asociatia-act-for-tomorrow',
                'asociatia-ana-si-copiii',
                'asociatia-animal-society',
                'forumapulum',
                'asociatia-ateliere-fara-frontiere',
                'asociatia-blondie',
                'cepec',
                'clubul-cainilor-utilitari',
                'daruieste-viata',
                'asociatia-edit',
                'asociatia-ecoassist-iniiativa-plantam-fapte-bune-in-romania',
                'geeks',
                'gifted',
                'growupromania',
                'asociatia-habitat-for-humanity-romania',
                'junior-achievement-romania',
                'asociatia-lume-buna',
                'asociatia-magic',
                'ovidiuro',
                'asociatia-pavel',
                'padureacopiilor',
                'asociatia-parcul-natural-vacaresti',
                'asociatia-pas-cu-pas-oradea',
                'asociatia-pentru-educatie-digitala-bigger-picture',
                'preocupati-de-viitor',
                'asociatia-pro-vita-bucuresti',
                'asociatia-romana-de-dezbateri-oratorie-si-retorica-ardor',
                'asociatia-salvati-flora-si-fauna-deltei-dunarii',
                'asociatia-samas',
                'asociatia-sansa-ta',
                'asociatia-semper-musica',
                'asociatia-solar-decatlon-bucuresti',
                'the-social-incubator',
                'asociatia-unu-si-unu',
                'wwf',
                'zi-de-bine',
                'centrul-pentru-politici-durabile-ecopolis',
                'asociatia-centrul-step-by-step-pentru-educatie-si-dezvoltare-profesionala',
                'fundatia-adapostul-speranta',
                'fundatia-romanian-angel-appeal',
                'fundatia-comunitara-bucuresti',
                'fundatia-conservation-carpathia',
                'fundatia-crucea-alb-galbena',
                'fundatia-serviciilor-sociale-bethany',
                'fundatiaenescu',
                'fundatia-hospice-casa-sperantei',
                'fundatia-impreuna-pentru-solidaritate-sociala',
                'fundatia-inocenti-bucuresti',
                'izvorulalb',
                'fundatianoiorizonturi',
                'fundatia-pact',
                'fundatia-regala-margareta-a-romaniei',
                'rolda',
                'world-vision-romania',
                'hopeandhomesromania',
                'asociatia-institutul-de-cercetare-in-permacultura-din-romania',
                'asociatia-mai-mult-verde',
                'mihaieminescutrust',
                'organizatia-umanitara-concordia',
                'httpwwwsalvaticopiiirodoilasuta',
                'sor',
                'sos-satele-copiilor-romania',
                'viitorplus',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in nesle_ngos])
            self.template_values['company_name'] = u'NESTLÉ'

        elif self.is_digi_subdomain:
            digi_ngos = [
                'angels-down-friends',
                'asociatia-ateliere-fara-frontiere',
                'asociatia-orizont-de-inger',
                'casiopeea',
                'code-for-romania',
                'hopeandhomesromania',
                'world-vision-romania',
                'httpwwwsalvaticopiiirodoilasuta',
                'sos-satele-copiilor-romania',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in digi_ngos])
            self.template_values['company_name'] = 'DIGI'

        elif self.is_raiffeisen_subdomain:
            raiffeisen_ngos = [
                'asociatia-civica',
                'asociatia-coolturala-noua-ne-pasa',
                'fanzin',
                'asociatia-dream-project',
                'asociatia-green-revolution',
                'asociatia-hercules',
                'yuppicamp',
                'asociatia-romana-de-dezbateri-oratorie-si-retorica-ardor',
                'sonoro',
                'asociatia-studentilor-francofoni-din-iasi',
                'runinbucharest',
                'code-for-romania',
                'fundatia-alma-mater-napocensis',
                'fundatia-cartea-calatoare',
                'fundatia-dezvoltarea-popoarelor-filiala-cluj',
                'fundatia-hategan',
                'fundatia-leaders',
                'fundatia-light-into-europe',
                'fundatia-regala-margareta-a-romaniei',
                'fundatia-cmu-regina-maria',
                'fundatia-united-way-romania',
                'aspen-romania',
                'junior-achievement-romania',
                'tasuleasa-social',
                'teach-for-romania',
                'ovidiuro',
                'agora-debate',
                'fundatia-worldskills-romania',
                'asociatia-pentru-educatie-digitala-bigger-picture',
                'bancadealimentecluj',
                'seeding-knowledge',
                'fundatia-comunitara-bucuresti',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in raiffeisen_ngos])
            self.template_values['company_name'] = 'Raiffeisen Bank'

        elif self.is_dbo_subdomain:
            dbo_ngos = [
                'asociatia-cartierul-creativ',
                'gaming-week',
                'rgda',
                'women-in-games-romania',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in dbo_ngos])
            self.template_values['company_name'] = 'DBO People'

        elif self.is_ursus_subdomain:
            ursus_ngos = [
                'asociatia-reality-check',
                'freemiorita',
                'asociatia-ateliere-fara-frontiere',
                'fundatia-comunitara-bucuresti',
                'fundatia-comunitara-buzau',
                'arcen',
                'media-dor',
                'carusel',
                'alianta-pentru-lupta-impotriva-alcoolismului-si-toxicomaniilor-aliat',
                'fundatia-fara',
                'fundatia-motivation-romania',
                'amais',
                'asociatia-sf-ana',
                'accept',
                'asociatia-activewatch',
                'fundatia-cpe-centrul-parteneriat-pentru-egalitate',
                'asociatia-lrnty-learnity',
                'asociatia-de-a-arhitectura',
                'teach-for-romania',
                'book-land',
                'asociatia-centrul-step-by-step-pentru-educatie-si-dezvoltare-profesionala',
                'asociatia-touched-romania',
                'centrul-de-dezvoltare-curriculara-si-studii-de-gen-filia',
                'fundatia-pentru-smurd',
                'rerise',
                'societatea-nationala-de-cruce-rosie-din-romania-filiala-sector-6-bucuresti',
                'policy-center-for-roma-and-minorities',
                'fundatia-conservation-carpathia',
                'asociatia-parcul-natural-vacaresti',
                'padureacopiilor',
                'liliecii-din-mediul-urban',
                'asociatia-robi',
                'asociatia-pentru-protectia-animalelor-kola-kariola',
                'asociatia-little-people-romania',
                'inimacopiilor',
                'fundatia-cmu-regina-maria',
                'asociatia-magic',
                'organizatia-umanitara-concordia',
                'ajungemmari',
                'fundatia-pentru-voi',
                'fundatia-united-way-romania',
                'code-for-romania',
                'cartea-daliei',
                'codette',
                'cere-participare',
                'fundatia-pact',
                'funky',
                'fundatia-special-olympics-din-romania',
                'asociatia-climb-again',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in ursus_ngos])
            self.template_values['company_name'] = 'Ursus'
            self.template_values['custom_header'] = True
            self.template_values['custom_note'] = True

        elif self.is_carrefour_subdomain:
            carrefour_ngos = [
                'crucea-rosie-romana',
                'httpwwwsalvaticopiiirodoilasuta',
                'asociatia-ana-si-copiii',
                'fundatia-hospice-casa-sperantei',
                'fundatia-cmu-regina-maria',
                'policy-center-for-roma-and-minorities',
                'asociatia-ateliere-fara-frontiere',
                'asociatia-zambetul-ingerilor',
                'fundatia-pentru-dezvoltarea-agriculturii',
            ]
            ngos = get_multi([Key(NgoEntity, k) for k in carrefour_ngos])
            self.template_values['company_name'] = 'Carrefour'

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

        now = datetime.now()
        # if we are not on a subdomain page, compute some stats
        if not self.template_values.get('company_name'):
            self.template_values["stats"] = {
                "ngos": NgoEntity.query().count(),
                "forms": Donor.query(Donor.date_created > datetime(now.year, 1, 1)).count()
            }

        self.template_values["current_year"] = now.year

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
        self.template_values["title"] = u"Asociații"

        ngos = NgoEntity.query(NgoEntity.active == True).fetch()
        self.template_values["ngos"] = ngos
        self.template_values["DEFAULT_NGO_LOGO"] = DEFAULT_NGO_LOGO

        # render a response
        self.render()

class TermsHandler(BaseHandler):
    template_name = 'terms.html'
    def get(self):

        self.template_values["title"] = "Termeni și condiții"

        # render a response
        self.render()

class NoteHandler(BaseHandler):
    template_name = 'note.html'
    def get(self):

        self.template_values["title"] = "Notă de informare"

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

        self.template_values["title"] = "Politica de confidențialitate"

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
