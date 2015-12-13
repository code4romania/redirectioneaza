


import os



# gcloud auth login
# gcloud config set project donezsieu-server

# gcloud preview app run ./app.yaml
# 
# DEPLOY
# LESS
# cd ./static/ && lessc css/main.less > css/main.css --clean-css="--s1 --advanced --compatibility=ie8" && cd ..
# 
# gcloud config set project donezsieu-server
# gcloud preview app deploy ./app.yaml --version 6 --promote
# gcloud preview app deploy ./app.yaml --version 17 --no-promote

# minify-css && gcloud preview app deploy ./app.yaml --version 14


# AWS CONNECT
# ssh -i main-server-key.pem ec2-user@52.10.187.83
# commands:
# ps aux | grep python
# kill -9 
# nohup python main.py &
# 


# if we are currently in production
DEV = os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')
# use this to simulate production
# DEV = False

PRODUCTION = not DEV


# used to communicate with aws
SECRET_KEY = "B1={kpE_4To5ZSJW=hNx(EYDj0-f|YT8uz5*SU6iA~.A+]aWSC#lmu;<Hc|T^V@-:#|+g0b<[+toRMtyqdtEDJ$%o4$>_yRTxbsh}%a|k)BS}u;dU~%Da;;SDhmZFl[_Wpr#U?A8"
AWS_PDF_URL = "http://ec2-52-28-113-53.eu-central-1.compute.amazonaws.com:8090" if PRODUCTION else "http://127.0.0.1:8090"


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
    # make sure the certificate is valid
    "Public-Key-Pins-Report-Only": 'pin-sha256="wuvbD/BvVfYoATqByqmg/6/XWyvmA+yeQImG75l2ous=";pin-sha256="6X0iNAQtPIjXKEVcqZBwyMcRwq1yW60549axatu3oDE=";pin-sha256="h6801m+z8v3zbgkRHpq6L29Esgfzhj89C1SyUCOQmqU=";max-age=2592000;report-uri="https://report-uri.io/report/donezsieu/reportOnly";includeSubdomains',

    # don't allow the site to be embeded
    "X-Frame-Options": "Deny",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy-Report-Only": "default-src 'self' ; script-src 'self' 'unsafe-eval' 'sha256-wwUprMhWJHcJgH7bVT8BB8TYRW7F8WDk5qBJvaLAsEw=' https://maxcdn.bootstrapcdn.com https://ajax.googleapis.com https://www.google.com https://www.gstatic.com https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https://maxcdn.bootstrapcdn.com https://fonts.googleapis.com; img-src 'self' https://donezsieu-static.s3.amazonaws.com; font-src 'self' https://fonts.gstatic.com https://maxcdn.bootstrapcdn.com; connect-src 'self' https://donezsieu-static.s3.amazonaws.com; media-src 'none' ; object-src 'none' ; child-src https://www.google.com/recaptcha/; frame-ancestors 'none' ; form-action 'self' ; reflected-xss block; report-uri https://report-uri.io/report/donezsieu/reportOnly;"
}

# ===================
# Recaptcha API Keys
# ===================
# 
# The public and private key
CAPTCHA_PUBLIC_KEY = "6Lc58hITAAAAAEy-owjeigG_x9FuPQqlZJRHEE6O" if PRODUCTION else "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
CAPTCHA_PRIVATE_KEY = "6Lc58hITAAAAADeRUDDFHJlzSVXKL6L7f-KukyZs" if PRODUCTION else "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
CAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
CAPTCHA_POST_PARAM = "g-recaptcha-response"

