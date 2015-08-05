
import webapp2

from appengine_config import SESSION_SECRET_KEY

from webapp2_extras import routes
from webapp2 import Route as r

# the public part of the app
from controllers.site import *

from controllers.ngo import NgoHandler, TwoPercentHandler, TwoPercent2Handler, DonationSucces


config = {
    'webapp2_extras.auth': {
        'user_model': 'models.user.User',
        'user_attributes': ['name']
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
        r('/cont-nou',  handler=NewAccountHandler),
    
        r('/<ngo_url>', handler=NgoHandler),

        # not a good idea
        # r('/<ngo_url>/2%',          handler=TwoPercentHandler),
        r('/<ngo_url>/doilasuta',           handler=TwoPercentHandler),
        r('/<ngo_url>/doilasuta/pas-2',     handler=TwoPercent2Handler),
        r('/<ngo_url>/doilasuta/succes',    handler=DonationSucces),
    ],
    debug=True,
    config=config
)

# http://blog.abahgat.com/2013/01/07/user-authentication-with-webapp2-on-google-app-engine/
# https://github.com/abahgat/webapp2-user-accounts
# https://github.com/abahgat/webapp2-user-accounts/blob/master/main.py
# https://github.com/abahgat/webapp2-user-accounts/blob/master/models.py
# http://gosurob.com/post/20024043690/gaewebapp2accounts