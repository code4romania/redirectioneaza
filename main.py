from controllers.site import *
from controllers.account_management import *
from controllers.my_account import *
from controllers.api import *
from controllers.admin import *
from controllers.ngo import NgoHandler, TwoPercentHandler, DonationSucces
from cron import NgoRemoveForms


# TESTING PURPOSES ONLY
# TODO Remove this, move into a separate manage.py file for management controls
#
# db.drop_all()
#
# db.create_all()
#
# from utils import load_dummy_data
#
# load_dummy_data()

# TESTING PURPOSES ONLY


def register_route(route, **kwargs):
    app.add_url_rule(route, view_func=kwargs['handler'].as_view(kwargs.get('name', route)))


# the public part of the app
register_route('/', handler=HomePage)
register_route('/ong', handler=ForNgoHandler)

# TODO Find out if this is still the case
# backup in case of old urls. to be removed
register_route('/pentru-ong-uri', handler=ForNgoHandler)

register_route('/asociatii', handler=NgoListHandler)

register_route('/termeni', handler=TermsHandler)
# TODO Find out why did we need a second one here
# register_route('/TERMENI',           handler=TermsHandler)
register_route('/nota-de-informare', handler=NoteHandler, name='note')
register_route('/politica', handler=PolicyHandler)
register_route('/despre', handler=AboutHandler)

# account management
register_route('/cont-nou', handler=SignupHandler)
register_route('/login', handler=LoginHandler, name='login')
register_route('/logout', handler=LogoutHandler, name='logout')

register_route('/forgot', handler=ForgotPasswordHandler, name='forgot')

# verification url: used for signup, and reset password

# TODO Set up regex in routes, for example /[pv]/[a-z]+[-][1-9]+
register_route('/verification/<type>/<user_id>-<signup_token>', handler=VerificationHandler, name='verification')
register_route('/password', handler=SetPasswordHandler, name='password')

# # my account
register_route('/contul-meu', handler=MyAccountHandler, name='contul-meu')
register_route('/asociatia', handler=NgoDetailsHandler, name='asociatia')
register_route('/date-cont', handler=MyAccountDetailsHandler, name='date-contul-meu')

register_route('/api/ngo/check-url/<ngo_url>', handler=CheckNgoUrl, name='api-ngo-check-url')
register_route('/api/ngo/upload-url', handler=GetUploadUrl, name='api-ngo-upload-url')
register_route('/api/ngo/form/<ngo_url>', handler=GetNgoForm, name='api-ngo-form-url')
register_route('/api/ngos', handler=NgosApi, name='api-ngos')

# # ADMIN HANDLERS
register_route('/admin', handler=AdminHandler, name='admin')
register_route('/admin/conturi', handler=UserAccounts, name='admin-users')
register_route('/admin/campanii', handler=SendCampaign, name='admin-campanii')
register_route('/admin/ong-nou', handler=AdminNewNgoHandler, name='admin-ong-nou')
register_route('/admin/<ngo_url>', handler=AdminNgoHandler, name='admin-ong')

register_route('/<ngo_url>', handler=NgoHandler, name="ngo-url")
register_route('/catre/<ngo_url>', handler=NgoHandler)

register_route('/<ngo_url>/doilasuta', handler=TwoPercentHandler, name="twopercent")
register_route('/<ngo_url>/doilasuta/succes', handler=DonationSucces, name="ngo-twopercent-success")
register_route('/cron', handler=NgoRemoveForms, name="ngo-remove-form")

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
