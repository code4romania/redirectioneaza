
import webapp2

from appengine_config import SESSION_SECRET_KEY

from webapp2_extras import routes
from webapp2 import Route as r

# the public part of the app
from controllers.site import *

from controllers.ngo import NgoHandler, TwoPercentHandler, TwoPercent2Handler, DonationSucces




config = {}
config['webapp2_extras.sessions'] = dict(secret_key= SESSION_SECRET_KEY)

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
