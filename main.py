
import webapp2

from appengine_config import SESSION_SECRET_KEY

from webapp2_extras import routes
from webapp2 import Route as r

# the public part of the app
from controllers.site import *
from controllers.account_management import *
from controllers.my_account import MyAccountHandler, NgoDetailsHandler, NgoDonationsHandler, NgoTwoPercentHandler

from controllers.ngo import NgoHandler, TwoPercentHandler, TwoPercent2Handler, DonationSucces


config = {
    'webapp2_extras.auth': {
        'user_model': 'models.user.User',
        'user_attributes': ['first_name']
    },
    # by default the session backend is the cookie
    # cookie_name: session
    # session_max_age: None => until the client is closed
    'webapp2_extras.sessions': {
        'secret_key': SESSION_SECRET_KEY
    }
}

app = webapp2.WSGIApplication([
        r('/',          handler=HomePage),

        r('/despre',    handler=AboutHandler),
        
        r('/cont-nou',  handler=SignupHandler),
        r('/login',     handler=LoginHandler, name='login'),
        r('/logout',    handler=LogoutHandler, name='logout'),

        r('/forgot',    handler=ForgotPasswordHandler, name='forgot'),
        r('/password',  handler=SetPasswordHandler),
        r('/<type:v|p>/<user_id:\d+>-<signup_token:.+>', handler=VerificationHandler, name='verification'),
        
        r('/contul-meu',        handler=MyAccountHandler, name='contul-meu'),
        r('/asociatia',         handler=NgoDetailsHandler, name='asociatia'),

        r('/donatii',           handler=NgoDonationsHandler, name='donatii'),
        r('/donatii/doilasuta', handler=NgoTwoPercentHandler, name='donatii-doilasuta'),

        r('/<ngo_url>',         handler=NgoHandler, name="ngo-url"),
        r('/catre/<ngo_url>',   handler=NgoHandler),

        r('/<ngo_url>/doilasuta',           handler=TwoPercentHandler),
        r('/<ngo_url>/doilasuta/pas-2',     handler=TwoPercent2Handler),
        r('/<ngo_url>/doilasuta/succes',    handler=DonationSucces),

    ],
    debug=True,
    config=config
)
