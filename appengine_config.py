# -*- coding: utf-8 -*-

import os


from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder.
vendor.add('lib')


# in order to not promote the current version
# gcloud config set app/promote_by_default false

# gcloud auth login
# gcloud config set project donezsieu-server

# DEPLOY
# LESS
# minify-css
# 
# gcloud config set project donezsieu-server
# gcloud app deploy ./app.yaml --version 26 --promote
# gcloud app deploy ./app.yaml --version 26 --no-promote

# minify-css && gcloud app deploy ./app.yaml --version 14

# if we are currently in production
DEV = os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')
# use this to simulate production
# DEV = False

PRODUCTION = not DEV

# the year when the site started
# used to create an array up to the current year
START_YEAR = 2016

USER_UPLOADS_FOLDER = 'uploads'
USER_FORMS = 'documents'

# where all the jinja2 templates should be located
VIEWS_FOLDER = "/views"

DEV_DEPENDECIES_LOCATION = "/bower_components"
TITLE = "redirectioneaza.ro"

SESSION_SECRET_KEY = "JgW`l2hZa*WV+z >}{T~Snq`DD1s@S#[Z7L>~.-;]t.7y2%gU)A^?ZTDyn/~kDh}RZA:/BVo7cI@TeA2Dll+0M#z|{,V*8`90VaV^`Cj&"


# ADMIN
BASE_ADMIN_LINK = "/admin"

LIST_OF_COUNTIES = ['Alba', 'Arad', 'Arges', 'Bacau', 'Bihor', 'Bistrita-Nasaud', 'Botosani', 'Braila', 'Brasov', 'Buzau', 'Calarasi', 'Caras-Severin', 'Cluj', 'Constanta', 'Covasna', 'Dambovita', 'Dolj', 'Galati', 'Giurgiu', 'Gorj', 'Harghita', 'Hunedoara', 'Ialomita', 'Iasi', 'Ilfov', 'Maramures', 'Mehedinti', 'Mures', 'Neamt', 'Olt', 'Prahova', 'Salaj', 'Satu Mare', 'Sibiu', 'Suceava', 'Teleorman', 'Timis', 'Tulcea', 'Valcea', 'Vaslui', 'Vrancea']

CONTACT_FORM_URL = "https://docs.google.com/forms/d/1PdigxpzW1omlTtexfu-gXEPEJmkiEltGLBaTQ8n-nk8/viewform"
CONTACT_EMAIL_ADDRESS = "redirectioneaza@code4.ro"


# ============================
# Additional response headers
# ============================
# 
# Tis headers are added for extra security
HTTP_HEADERS = {
    # lgarron at chromium dot org 
    # https://hstspreload.appspot.com/
    # for https everywhere, and on subdomains, 1 year
    "Strict-Transport-Security": "max-age=31536000; includeSubdomains; preload",

    # don't allow the site to be embeded
    "X-Frame-Options": "Deny",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    # "Content-Security-Policy": "default-src 'self'; script-src 'self' 'sha256-wwUprMhWJHcJgH7bVT8BB8TYRW7F8WDk5qBJvaLAsEw=' https://maxcdn.bootstrapcdn.com https://ajax.googleapis.com https://www.google.com https://www.gstatic.com https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https://maxcdn.bootstrapcdn.com https://fonts.googleapis.com; img-src 'self' https://storage.googleapis.com/ https://www.google-analytics.com/; font-src 'self' https://fonts.gstatic.com https://maxcdn.bootstrapcdn.com; media-src 'none'; object-src 'none'; child-src https://www.google.com/recaptcha/; frame-ancestors 'none'; form-action 'self'; report-uri https://donezsieu.report-uri.io/r/default/csp/enforce;"
}



# ===================
# Recaptcha API Keys
# ===================
# 
# The public and private key
# CAPTCHA_PUBLIC_KEY = "6Lc58hITAAAAAEy-owjeigG_x9FuPQqlZJRHEE6O" if PRODUCTION else "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
# CAPTCHA_PRIVATE_KEY = "6Lc58hITAAAAADeRUDDFHJlzSVXKL6L7f-KukyZs" if PRODUCTION else "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
# CAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
# CAPTCHA_POST_PARAM = "g-recaptcha-response"


CAPTCHA_PUBLIC_KEY = "6LfQeBkUAAAAAPUxei7PQYfwrDnB8kq6l4xiHTJm" if PRODUCTION else "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
CAPTCHA_PRIVATE_KEY = "6LfQeBkUAAAAAKwV-nlANe-ylQa7wO_5nGhj6sBH" if PRODUCTION else "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
CAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
CAPTCHA_POST_PARAM = "g-recaptcha-response"


ANAF_OFFICES = {
    'alba': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice ALBA",
        "address": u"Alba Iulia, Str. Primăverii nr. 10 C.P. 510110"
    },
    'arad': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice ARAD",
        "address": u"B-dul Revoluţiei, nr. 77, C.P. 310130, ARAD"
    },
    'arges': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice ARGEŞ",
        "address": u"B-dul Republicii nr. 118, Piteşti, C.P.110050"
    },
    'bacau': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BACĂU",
        "address": u"Str. Dumbrava Roşie nr. 1-3, C.P. 600045, BACĂU"
    },
    'bihor': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BIHOR",
        "address": u"Str.Dimitrie Cantemir nr.2B, Oradea, C.P. 410519"
    },
    'bistrita-nasaud': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BISTRIŢA-NĂSĂUD",
        "address": u"Str. Decembrie, nr. 6-8, Bistriţa, C.P. 420080"
    },
    'botosani': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BOTOŞANI",
        "address": u"Piaţa Revolutiei nr.5, C.P. 710236, BOTOŞANI"
    },
    'braila': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BRĂILA",
        "address": u"Str. Delfinului nr. 1, C.P. 810210, BRĂILA"
    },
    'brasov': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BRAŞOV",
        "address": u"Bd. Mihail Kogălniceanu nr. 7, C.P. 500090, BRAŞOV"
    },
    'buzau': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice BUZĂU",
        "address": u"Str. Unirii nr. 209 , C.P. 120191, BUZĂU"
    },
    'calarasi': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice CĂLĂRAŞI",
        "address": u"Str. Eroilor, nr.6-8, C.P.910005,"
    },
    'caras-severin': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice CARAŞ-SEVERIN",
        "address": u"Str. Domanului nr. 2, Reşiţa, C.P. 320071"
    },
    'cluj': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice CLUJ",
        "address": u"Piaţa Avram Iancu nr. 19, Cluj-Napoca"
    },
    'constanta': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice CONSTANŢA",
        "address": u"Str. I.G. Duca nr. 18, CONSTANŢA"
    },
    'covasna': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice COVASNA",
        "address": u"Str. Bem Jozef nr.9, Sfântu Gheorghe, C.P. 520023"
    },
    'dambovita': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice DÂMBOVIŢA",
        "address": u"Calea Domnească nr.166, Târgovişte, C.P.130003"
    },
    'dolj': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice DOLJ",
        "address": u"Str. Mitropolit Firmilian nr.2, Craiova, CP 200761"
    },
    'galati': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice GALAŢI",
        "address": u"Str. Brăilei Nr.33, CP  800076, GALAŢI"
    },
    'giurgiu': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice GIURGIU",
        "address": u"Sos.Bucureşti nr.12 , C.P. 080045"
    },
    'gorj': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice GORJ",
        "address": u"Str. Siretului nr. 6, Târgu Jiu, C.P. 210190"
    },
    'harghita': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice HARGHITA",
        "address": u"Str.Rev.din Decembrie nr.20, Miercurea Ciuc, C.P. 530223"
    },
    'hunedoara': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice HUNEDOARA",
        "address": u"Str.Avram Iancu Bl.H3 Parter, Deva, C.P. 330025"
    },
    'ialomita': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice IALOMIŢA",
        "address": u"Str. Matei Basarab nr. 14, Slobozia, C.P. 920031"
    },
    'iasi': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice IAŞI",
        "address": u"Str. Anastasie Panu nr.26, C.P. 700020"
    },
    'ilfov': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice ILFOV",
        "address": u"Str Lucreţiu Pătrăşcanu nr 10, sector 3, Bucureşti"
    },
    'maramures': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice MARAMUREŞ",
        "address": u"Str. Serelor, nr. 2/A, Baia Mare, C.P. 430333"
    },
    'mehedinti': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice MEHEDINŢI",
        "address": u"Piaţa Radu Negru nr.1, Drobeta-Turnu Severin"
    },
    'mures': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice MUREŞ",
        "address": u"Str. Gheorghe Doja nr. 1-3, Târgu Mureş"
    },
    'neamt': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice NEAMŢ",
        "address": u"Bd. Traian nr. 19 bis, Piatra Neamţ, C.P. 610137"
    },
    'olt': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice OLT",
        "address": u"Str. Arcului nr.2A, Slatina, C.P. 230039"
    },
    'prahova': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice PRAHOVA",
        "address": u"Str. Aurel Vlaicu nr. 22, Ploieşti, C.P. 100023"
    },
    'salaj': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice SĂLAJ",
        "address": u"Piaţa Iuliu Maniu, nr. 15, Zalău, C.P. 450016"
    },
    'satu mare': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice SATU MARE",
        "address": u"Piaţa Romană, nr. 3-5, CP 440012"
    },
    'sibiu': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice SIBIU",
        "address": u"Calea Dumbrăvii,  nr. 17, CP 550324"
    },
    'suceava': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice SUCEAVA",
        "address": u"Str. Vasile Bumbac nr.1, C.P.720003"
    },
    'teleorman': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice TELEORMAN",
        "address": u"Str. Dunării, nr. 188, Alexandria, C.P. 140046"
    },
    'timis': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice TIMIŞ",
        "address": u"Str. Gheorghe Lazăr nr.9B, Timişoara, C.P. 300081"
    },
    'tulcea': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice TULCEA",
        "address": u"Str.Babadag, Nr.163 bis, C.P.820112"
    },
    'valcea': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice VÂLCEA",
        "address": u"Str. G-ral Magheru nr. 17, Râmnicu Vâlcea"
    },
    'vaslui': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice VASLUI",
        "address": u"Str. Stefan cel Mare, nr. 56, C.P. 730171"
    },
    'vrancea': {
        "name": u"Administraţia Judeţeană a Finanţelor Publice VRANCEA",
        "address": u"Bd. Independentei nr. 24, Focşani, C.P.620112"
    },
    # bucuresti
    '1': {
        "name": u"Administraţia sectorului 1 a finanţelor publice",
        "address": u"Soseaua Bucuresti - Ploiesti, numarul 9-13"
    },
    '2': {
        "name": u"Administraţia sectorului 2 a finanţelor publice",
        "address": u"Str.Avrig nr.63, sector 2"
    },
    '3': {
        "name": u"Administraţia sectorului 3 a finanţelor publice",
        "address": u"Str.Lucreţiu Pătrăşcanu nr.10, sector 3, C.P. 030504"
    },
    '4': {
        "name": u"Administraţia sectorului 4 a finanţelor publice",
        "address": u"Bd. C.Brâncoveanu nr. 2, bl. 12, sector 4, C.P. 041447"
    },
    '5': {
        "name": u"Administraţia sectorului 5 a finanţelor publice",
        "address": u"Calea 13 Septembrie nr. 226, bloc. V 54, sector 5"
    },
    '6': {
        "name": u"Administraţia sectorului 6 a finanţelor publice",
        "address": u"Str. Popa Tatu nr.7, sector 1, C.P. 010801"
    }
}
