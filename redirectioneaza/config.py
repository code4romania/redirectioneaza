# -*- coding: utf-8 -*-
"""
This file contains configurations settings for the application
"""
# TODO: Cleanup unused settings
# TODO: Create Environment-Specific Configuration profiles that inherit from Base Configuration. Use config from object.

import os

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
DEV = os.environ.get('REDIR_ENVIRONMENT') == 'DEV'
# use this to simulate production
# DEV = False

DEV_SERVER_HOST, DEV_SERVER_PORT = 'localhost', 5000

PRODUCTION = os.environ.get('REDIR_ENVIRONMENT') == 'PROD'

# the year when the site started
# used to create an array up to the current year
START_YEAR = 2016

USER_UPLOADS_FOLDER = 'uploads'
USER_FORMS = 'documents'

# where all the jinja2 templates should be located
VIEWS_FOLDER = "/views"

DEV_DEPENDECIES_LOCATION = "/bower_components"
TITLE = "redirectioneaza.ro"

SESSION_SECRET_KEY = os.environ.get('SESSION_SECRET_KEY')

DEFAULT_NGO_LOGO = "https://storage.googleapis.com/redirectioneaza/logo_bw.png"

# ADMIN
BASE_ADMIN_LINK = "/admin"

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
CAPTCHA_PUBLIC_KEY = os.environ.get('CAPTCHA_PUBLIC_KEY') if PRODUCTION else "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
CAPTCHA_PRIVATE_KEY = os.environ.get(
    'CAPTCHA_PRIVATE_KEY') if PRODUCTION else "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
CAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
CAPTCHA_POST_PARAM = "g-recaptcha-response"
