# -*- coding: utf-8 -*-
"""
This file contains configurations settings for the application
"""
# TODO: Cleanup unused settings
# TODO: Create Environment-Specific Configuration profiles that inherit from Base Configuration. Use config from object.

from os import environ

# DEPLOY
# LESS
# minify-css

ENVIRONMENT = environ['REDIR_ENVIRONMENT']


class AppBaseConfig:
    # TODO Rethink this once migrated to another object store
    UPLOAD_FOLDER = 'storage'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class AppDevelopmentConfig(AppBaseConfig):
    REDIR_USERNAME = environ.get('REDIR_USERNAME')
    REDIR_PASSWORD = environ.get('REDIR_PASSWORD')
    REDIR_DBSERVER = environ.get('REDIR_DBSERVER')
    REDIR_DBPORT = environ.get('REDIR_DBPORT')
    REDIR_DBCATALOG = environ.get('REDIR_DBCATALOG')

    # Set up app configuration
    SQLALCHEMY_DATABASE_URI = \
        f'postgresql://{REDIR_USERNAME}:{REDIR_PASSWORD}@{REDIR_DBSERVER}:{REDIR_DBPORT}/{REDIR_DBCATALOG}'

    SECRET_KEY = environ.get('APP_SECRET_KEY')
    SECURITY_PASSWORD_SALT = environ.get('SECURITY_PASSWORD_SALT')
    MAIL_SENDGRID_API_KEY = environ.get('SENDGRID_API_KEY')
    DEV_SERVER_HOST, DEV_SERVER_PORT = 'localhost', 5000


CONFIG_BY_NAME = dict(
    DEV=AppDevelopmentConfig
)


# if we are currently in production
DEV = environ.get('REDIR_ENVIRONMENT') == 'DEV'

# use this to simulate production
# DEV = False

PRODUCTION = environ.get('REDIR_ENVIRONMENT') == 'PROD'

# the year when the site started
# used to create an array up to the current year
START_YEAR = 2016

# USER_UPLOADS_FOLDER = 'uploads'
# USER_FORMS = 'documents'

# where all the jinja2 templates should be located
#VIEWS_FOLDER = "/views"

DEV_DEPENDECIES_LOCATION = "/bower_components"

TITLE = "redirectioneaza.ro"

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
CAPTCHA_PUBLIC_KEY = environ.get('CAPTCHA_PUBLIC_KEY') if PRODUCTION else "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
CAPTCHA_PRIVATE_KEY = environ.get(
    'CAPTCHA_PRIVATE_KEY') if PRODUCTION else "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
CAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
CAPTCHA_POST_PARAM = "g-recaptcha-response"
