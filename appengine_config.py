


import os



# gcloud auth login
# gcloud config set project donezsieu-server

# gcloud preview app run ./app.yaml
# 
# DEPLOY
# LESS
# cd ./static/ && lessc css/main.less > css/main.css && cd ..
# 
# gcloud config set project donezsieu-server
# gcloud preview app deploy ./app.yaml --version 6 --set-default
# gcloud preview app deploy ./app.yaml --version 7


# AWS CONNECT
# ssh -i main-server-key.pem ec2-user@52.10.187.83


# if we are currently in production
DEV = os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')
# use this to simulate production
# DEV = False

PRODUCTION = not DEV


# used to communicate with aws
SECRET_KEY = "B1={kpE_4To5ZSJW=hNx(EYDj0-f|YT8uz5*SU6iA~.A+]aWSC#lmu;<Hc|T^V@-:#|+g0b<[+toRMtyqdtEDJ$%o4$>_yRTxbsh}%a|k)BS}u;dU~%Da;;SDhmZFl[_Wpr#U?A8"
AWS_PDF_URL = "http://ec2-52-10-187-83.us-west-2.compute.amazonaws.com:8090" if PRODUCTION else "http://127.0.0.1:8090"


GEOIP_SERVICES = ["http://ip-api.com/json/{0}", "http://freegeoip.net/json/{0}"]

# where all the jinja2 templates should be located
VIEWS_FOLDER = "/views"

DEV_DEPENDECIES_LOCATION = "/bower_components"
TITLE = "donezsi.eu"

SESSION_SECRET_KEY = "JgW`l2hZa*WV+z >}{T~Snq`DD1s@S#[Z7L>~.-;]t.7y2%gU)A^?ZTDyn/~kDh}RZA:/B{Vo7cI@TeA2Dll+0M#z|{,V*8`90VaV^`Cj&"


# ADMIN
BASE_ADMIN_LINK = "/admin"

LIST_OF_COUNTIES = ['Alba', 'Arad', 'Arges', 'Bacau', 'Bihor', 'Bistrita-Nasaud', 'Botosani', 'Braila', 'Brasov', 'Buzau', 'Calarasi', 'Caras-Severin', 'Cluj', 'Constanta', 'Covasna', 'Dambovita', 'Dolj', 'Galati', 'Giurgiu', 'Gorj', 'Harghita', 'Hunedoara', 'Ialomita', 'Iasi', 'Ilfov', 'Maramures', 'Mehedinti', 'Mures', 'Neamt', 'Olt', 'Prahova', 'Salaj', 'Satu Mare', 'Sibiu', 'Suceava', 'Teleorman', 'Timis', 'Tulcea', 'Valcea', 'Vaslui', 'Vrancea']

CONTACT_FORM_URL = "https://docs.google.com/forms/d/1PdigxpzW1omlTtexfu-gXEPEJmkiEltGLBaTQ8n-nk8/viewform"
CONTACT_EMAIL_ADDRESS = "donez si eu <contact@donezsi.eu>"





# def webapp_add_wsgi_middleware(app):
#     from google.appengine.ext.appstats import recording
#     app = recording.appstats_wsgi_middleware(app)
#     return app

# appstats_CALC_RPC_COSTS = True