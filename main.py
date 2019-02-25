from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ

import sys
sys.path.insert(1, '/home/dev/assets/google-cloud-sdk/platform/google_appengine')
sys.path.insert(1, '/home/dev/assets/google-cloud-sdk/platform/google_appengine/lib/yaml/lib')
sys.path.insert(1, 'lib')

if 'google' in sys.modules:
    del sys.modules['google']

from core import app, db
from appengine_config import SESSION_SECRET_KEY, DEV
from controllers.site import *
from controllers.account_management import *
from controllers.my_account import *
# from controllers.api import *
# from controllers.admin import *
# from controllers.ngo import NgoHandler, TwoPercentHandler, DonationSucces
# from cron import cron_routes

db.drop_all()

db.create_all()
def setup_route(route, **kwargs):
    app.add_url_rule(route, view_func=kwargs['handler'].as_view(kwargs.get('name', route)))


# the public part of the app
setup_route('/',                  handler=HomePage)
setup_route('/ong',               handler=ForNgoHandler)

# backup in case of old urls. to be removed
setup_route('/pentru-ong-uri',    handler=ForNgoHandler)

setup_route('/asociatii',         handler=NgoListHandler)

setup_route('/termeni',           handler=TermsHandler)
setup_route('/TERMENI',           handler=TermsHandler)
setup_route('/nota-de-informare', handler=NoteHandler,    name='note')
setup_route('/politica',          handler=PolicyHandler)
setup_route('/despre',            handler=AboutHandler)

#account management
setup_route('/cont-nou',  handler=SignupHandler)
setup_route('/login',     handler=LoginHandler, name='login')
setup_route('/logout',    handler=LogoutHandler, name='logout')

setup_route('/forgot',    handler=ForgotPasswordHandler, name='forgot')

# verification url: used for signup, and reset password
# setup_route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>', handler=VerificationHandler, name='verification')
setup_route('/password',  handler=SetPasswordHandler)

# # my account
setup_route('/contul-meu',        handler=MyAccountHandler, name='contul-meu')
setup_route('/asociatia',         handler=NgoDetailsHandler, name='asociatia')
setup_route('/date-cont',         handler=MyAccountDetailsHandler, name='date-contul-meu')

# setup_route('/api/ngo/check-url/<ngo_url>',   handler=CheckNgoUrl,    name='api-ngo-check-url')
# setup_route('/api/ngo/upload-url',            handler=GetUploadUrl,   name='api-ngo-upload-url')
# setup_route('/api/ngo/form/<ngo_url>',        handler=GetNgoForm,     name='api-ngo-form-url')
# setup_route('/api/ngos',                      handler=NgosApi,        name='api-ngos')

# # ADMIN HANDLERS
# setup_route('/admin',             handler=AdminHandler,       name='admin')
# setup_route('/admin/conturi',     handler=UserAccounts,       name='admin-users')
# setup_route('/admin/campanii',    handler=SendCampaign,       name='admin-campanii')
# setup_route('/admin/ong-nou',     handler=AdminNewNgoHandler, name='admin-ong-nou')
# setup_route('/admin/<ngo_url>',   handler=AdminNgoHandler,    name='admin-ong')


# setup_route('/<ngo_url>',         handler=NgoHandler, name="ngo-url")
# setup_route('/catre/<ngo_url>',   handler=NgoHandler)

# setup_route('/<ngo_url>/doilasuta',           handler=TwoPercentHandler,  name="twopercent")
# setup_route('/<ngo_url>/doilasuta/succes',    handler=DonationSucces,     name="ngo-twopercent-success")

    # routes.PathPrefixRoute("/cron", cron_routes),
