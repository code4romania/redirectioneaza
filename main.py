
import webapp2
from os import environ

from appengine_config import SESSION_SECRET_KEY, DEV

from webapp2_extras import routes
from webapp2 import Route as r

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
        # the public part of the app
        r('/',                  handler="controllers.site.HomePage"),
        r('/pentru-ong-uri',    handler="controllers.site.ForNgoHandler"),
        r('/asociatii',         handler="controllers.site.NgoListHandler"),

        r('/termeni',    handler="controllers.site.TermsHandler"),
        r('/TERMENI',    handler="controllers.site.TermsHandler"),
        r('/politica',   handler="controllers.site.PolicyHandler"),

        # account management
        r('/cont-nou',  handler="controllers.account_management.SignupHandler"),
        r('/login',     handler="controllers.account_management.LoginHandler", name='login'),
        r('/logout',    handler="controllers.account_management.LogoutHandler", name='logout'),

        r('/forgot',    handler="controllers.account_management.ForgotPasswordHandler", name='forgot'),
        r('/password',  handler="controllers.account_management.SetPasswordHandler"),
        # verification url: used for signup, and reset password
        r('/<type:v|p>/<user_id:\d+>-<signup_token:.+>', handler="controllers.account_management.VerificationHandler", name='verification'),
        
        # my account
        r('/contul-meu',        handler="controllers.my_account.MyAccountHandler", name='contul-meu'),
        r('/asociatia',         handler="controllers.my_account.NgoDetailsHandler", name='asociatia'),
        r('/date-cont',         handler="controllers.my_account.MyAccountDetailsHandler", name='date-contul-meu'),

        r('/api/ngo/check-url/<ngo_url>', handler="controllers.api.CheckNgoUrl", name='api-ngo-check-url'),
        r('/api/ngo/upload-url',          handler="controllers.api.GetUploadUrl", name='api-ngo-upload-url'),

        # ADMIN HANDLERS
        r('/admin',             handler="controllers.admin.AdminHandler",       name='admin'),
        r('/admin/conturi',     handler="controllers.admin.UserAccounts",       name='admin-users'),
        r('/admin/campanii',    handler="controllers.admin.SendCampaign",       name='admin-campanii'),
        r('/admin/ong-nou',     handler="controllers.admin.AdminNewNgoHandler", name='admin-ong-nou'),
        r('/admin/<ngo_url>',   handler="controllers.admin.AdminNgoHandler",    name='admin-ong'),


        r('/<ngo_url>',         handler=NgoHandler, name="ngo-url"),
        r('/catre/<ngo_url>',   handler=NgoHandler),

        r('/<ngo_url>/doilasuta',           handler=TwoPercentHandler,  name="twopercent"),
        r('/<ngo_url>/doilasuta/pas-2',     handler=TwoPercent2Handler, name="twopercent-step-2"),
        r('/<ngo_url>/doilasuta/succes',    handler=DonationSucces,     name="ngo-twopercent-success"),

    ],
    debug=True,
    config=config
)
