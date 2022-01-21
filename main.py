
import webapp2
from os import environ

from appengine_config import SESSION_SECRET_KEY, DEV

from webapp2_extras import routes
from webapp2 import Route as r

from controllers.site import *
from controllers.account_management import *
from controllers.my_account import *
from controllers.api import *
from controllers.admin import *
from controllers.ngo import NgoHandler, TwoPercentHandler, DonationSucces

from cron import cron_routes

config = {
    'webapp2_extras.auth': {
        'user_model': 'models.user.User',
        'user_attributes': ['first_name']
    },
    # by default the session backend is the cookie
    # cookie_name: session
    # session_max_age: None => until the client is closed
    'webapp2_extras.sessions': {
        'secret_key': SESSION_SECRET_KEY,
        # just make it as the default
        'cookie_name': 'session',
        'cookie_args': {
            # make the cookie secure only if we are on production
            # we can't use the config DEV bool, because if we set that manually to False, in order 
            # to test prod locally, the cookie will not work
            # so make sure the cookie are set to secure only in production
            'secure': not environ.get('SERVER_SOFTWARE', 'Development').startswith('Development'),
            'httponly': True
        }
    }
}

# use string in dotted notation to be lazily imported
app = webapp2.WSGIApplication([
        routes.DomainRoute('ikea.redirectioneaza.ro', [
            webapp2.Route('/', handler=HomePage, name='ikea-home'),
        ]),

        # the public part of the app
        r('/',                  handler=HomePage,       name="home"),
        r('/ong',               handler=ForNgoHandler),
        
        # backup in case of old urls. to be removed
        r('/pentru-ong-uri',    handler=ForNgoHandler),
        
        r('/asociatii',         handler=NgoListHandler),

        r('/termeni',           handler=TermsHandler),
        r('/TERMENI',           handler=TermsHandler),
        r('/nota-de-informare', handler=NoteHandler,    name='note'),
        r('/politica',          handler=PolicyHandler),
        r('/despre',            handler=AboutHandler),

        # account management
        r('/cont-nou',  handler=SignupHandler),
        r('/login',     handler=LoginHandler, name='login'),
        r('/logout',    handler=LogoutHandler, name='logout'),

        r('/forgot',    handler=ForgotPasswordHandler, name='forgot'),
        
        # verification url: used for signup, and reset password
        r('/<type:v|p>/<user_id:\d+>-<signup_token:.+>', handler=VerificationHandler, name='verification'),
        r('/password',  handler=SetPasswordHandler),
        
        # my account
        r('/contul-meu',        handler=MyAccountHandler, name='contul-meu'),
        r('/asociatia',         handler=NgoDetailsHandler, name='asociatia'),
        r('/date-cont',         handler=MyAccountDetailsHandler, name='date-contul-meu'),

        r('/api/ngo/check-url/<ngo_url>',   handler=CheckNgoUrl,    name='api-ngo-check-url'),
        r('/api/ngo/upload-url',            handler=GetUploadUrl,   name='api-ngo-upload-url'),
        r('/api/ngo/form/<ngo_url>',        handler=GetNgoForm,     name='api-ngo-form-url'),
        r('/api/ngos',                      handler=NgosApi,        name='api-ngos'),

        # ADMIN HANDLERS
        r('/admin',             handler=AdminHome,          name='admin'),
        r('/admin/organizatii', handler=AdminNgosList,      name='admin-nogs'),
        r('/admin/conturi',     handler=UserAccounts,       name='admin-users'),
        r('/admin/campanii',    handler=SendCampaign,       name='admin-campanii'),
        r('/admin/ong-nou',     handler=AdminNewNgoHandler, name='admin-ong-nou'),
        r('/admin/<ngo_url>',   handler=AdminNgoHandler,    name='admin-ong'),

        r('/<ngo_url>',           handler=TwoPercentHandler,  name="twopercent"),
        r('/<ngo_url>/succes',    handler=DonationSucces,     name="ngo-twopercent-success"),

        r('/<ngo_url>/doilasuta', handler=NgoHandler,         name="ngo-url"),

        routes.PathPrefixRoute("/cron", cron_routes),
    ],
    debug=True,
    config=config
)

# error handling for 404 and 500
# imported from controllers.site
# app.error_handlers[404] = NotFoundPage
# app.error_handlers[500] = InternalErrorPage