


import os


from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder.
vendor.add('lib')


# in order to not promote the current version
# gcloud config set app/promote_by_default false

# gcloud auth login
# gcloud config set project donezsieu-server

# gcloud preview app run ./app.yaml
# 
# DEPLOY
# LESS
# cd ./static/ && lessc css/main.less > css/main.css --clean-css="--s1 --advanced --compatibility=ie8" && cd ..
# 
# gcloud config set project donezsieu-server
# gcloud app deploy ./app.yaml --version 26 --promote
# gcloud app deploy ./app.yaml --version 26 --no-promote

# minify-css && gcloud app deploy ./app.yaml --version 14

# create pdf
# curl 'http://localhost:8080/asoc/doilasuta' -H 'Cookie: auth="e30\075|1452959992|64942700a0ed7400d63342ee6c806290cfa05e"; session="e30\075|1452960748|f2a8976fefe8063a66a4b7d4aed8129fdf95fa19"' -H 'Origin: http://localhost:8080' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: en-US,en;q=0.8,ro;q=0.6,es;q=0.4' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Referer: http://localhost:8080/asoc/doilasuta' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --data 'nume=dsadada&prenume=dsadasd&tatal=L&cnp=1231231231231&strada=srt+sadadd&numar=333&bloc=A&scara=2&etaj=2&ap=22&localitate=Braila&judet=Brasov&agree=on&g-recaptcha-response=03AHJ_VuvCHxzhjqGzhJ6F0NdkSPy-BNVWATnVnvWuodInIzj_BvdFRF9WcuCti4UlDRg97s1sGE_7O4PYq2HGcORo0bS_W0txctdSfxLlrA0Co_7kYtLEUGYIYJW8JZbTVFgISJy_1UO-QPl6GXe5fmZMAusO6TQP6M1IVy0Q_bB20Mj2dgnw5qOQq5Tg7cDS_pCswLuWNt0PvDIXsPA4UGPN7yhq7MnvNJaXqFibyzox-81hMBLyeZYYld46TFJqNNbZh2JRbuvj0ZA00PGmD8uTVvFAVADW4vv-W5luRayfLvtmpgYrPFUhEQRfAzIkIhwE_GrjguRZxf0iAkaQ2HoZcq1xEKt8BuZLaZ10PUUmkFp1OHUSZpsDePFRRBen_fYf4Q89TMwSOsqZ54TIooraqobPFeHxIF7l4yby2dM5kBEQ6zk25_eRpAIvtiWrYW-UOkvh8zdAN8YHFbD09BA0RcKEGiv4N29_P4GKJbUHjpn_wDhVHEh-QKp5Awlg9PkKJUAT-9wiYCuzeK6o8FH6JW3t4Nt8eiTcpwutVPZX-DS-PieC9vW59fLPM77NutwbjL5wddlC58nw7D2Gg7s8-8Hv-wXKZ65WPJgFUlVndtGqRDBNq4AYl1pFa1Dzs8YFo6hDkWu2PIJwRIehmw-aC_1Cj3Ew65Ob9bkwN1EjGN8Q7DjI9F9VQy2LJvGCqDdZkbXMkOylULb6PUuqCbzc9st7ZNMqdcHoXlXmNn2qfVbCirQ0RFq1Jz1TEJHUsy00NAXNbEFenYFn5_LAO0uttiX2GizaloyOxhMZD4KlGdsrM-tL97JioSckvOspLjAsEgxruZTM22f0W93V60OiottRMFfW4vpJVRdQ2vUNMeFkXR-ZfCfF4RKwZwERKcvA6nvcfxwJ-d-qvXbQcC3FqK58M1jiELbYjR33Ko-BDFmjzU2GctU&ajax=true' --compressed
# add email
# curl 'http://localhost:8080/asoc/doilasuta/pas-2' -H 'Cookie: auth="e30\075|1452959992|64942700a0ed7400d6382342ee6c806290cfa05e"; session="eyJkb25vcl9pZCI6IjU5MTA5NzQ1MTA5MjM3NzYiLCJoYXNfY25wIjpmYWxzZX0\075|1452960759|b8a18e221f41e5dc858e3fa8d0534e0176fc8ae0"' -H 'Origin: http://localhost:8080' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: en-US,en;q=0.8,ro;q=0.6,es;q=0.4' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Referer: http://localhost:8080/asoc/doilasuta' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --data 'email=aaaa%40aaaa.com&tel=&ajax=true' --compressed

# if we are currently in production
DEV = os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')
# use this to simulate production
# DEV = False

PRODUCTION = not DEV

# the year when the site started
# used to create an array up to the current year
START_YEAR = 2016

# used to communicate with aws
SECRET_KEY = "B1={kpE_4To5ZSJW=hNx(EYDj0-f|YT8uz5*SU6iA~.A+]aWSC#lmu;<Hc|T^V@-:#|+g0b<[+toRMtyqdtEDJ$%o4$>_yRTxbsh}%a|k)BS}u;dU~%Da;;SDhmZFl[_Wpr#U?A8"
AWS_PDF_URL = "http://main-balancer-1246647494.eu-west-1.elb.amazonaws.com:8090/" if PRODUCTION else "http://127.0.0.1:8090"

USER_UPLOADS_FOLDER = 'uploads'
USER_FORMS = 'documents'

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
    "Content-Security-Policy-Report-Only": "default-src 'self'; script-src 'self' 'unsafe-eval' 'sha256-wwUprMhWJHcJgH7bVT8BB8TYRW7F8WDk5qBJvaLAsEw=' https://maxcdn.bootstrapcdn.com https://ajax.googleapis.com https://www.google.com https://www.gstatic.com https://www.google-analytics.com; style-src 'self' https://maxcdn.bootstrapcdn.com https://fonts.googleapis.com; img-src 'self' https://storage.googleapis.com/donezsieu-bucket/; font-src 'self' https://fonts.gstatic.com https://maxcdn.bootstrapcdn.com; connect-src 'self' https://donezsieu-static.s3.amazonaws.com; media-src 'none'; object-src 'none'; child-src https://www.google.com/recaptcha/; frame-ancestors 'none'; form-action 'self'; reflected-xss block; report-uri https://donezsieu.report-uri.io/r/default/csp/reportOnly;"
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

