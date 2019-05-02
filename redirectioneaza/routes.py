"""
This file contains the routes defined by the application.
"""

from flask import send_from_directory

from redirectioneaza.controllers.account_management import *
from redirectioneaza.controllers.api import *
from redirectioneaza.controllers.my_account import *
from redirectioneaza.controllers.ngo import *
from redirectioneaza.controllers.site import *
from . import app


def register_route(route, **kwargs):
    """
    This method registers routes and binds them to Method Views
    :param route:
    :param kwargs:
    :return:
    """
    app.add_url_rule(route, view_func=kwargs['handler'].as_view(kwargs.get('name', route)))


# the public part of the app
register_route('/', handler=HomePage, name='index')
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

register_route('/verification/<token>', handler=VerificationHandler, name='verification')
register_route('/password', handler=SetPasswordHandler, name='password')

# # my account
register_route('/contul-meu', handler=MyAccountHandler, name='contul-meu')
register_route('/asociatia', handler=NgoDetailsHandler, name='asociatia')
register_route('/date-cont', handler=MyAccountDetailsHandler, name='date-contul-meu')

register_route('/api/ngo/check-url/<ngo_url>', handler=CheckNgoUrl, name='api-ngo-check-url')
register_route('/api/ngo/upload-url', handler=GetUploadUrl, name='api-ngo-upload-url')
register_route('/api/ngo/form/<ngo_url>', handler=GetNgoForm, name='api-ngo-form-url')
register_route('/api/ngos', handler=NgosApi, name='api-ngos')

register_route('/<ngo_url>', handler=NgoHandler, name="ngo-url")
register_route('/catre/<ngo_url>', handler=NgoHandler)
register_route('/<ngo_url>/doilasuta', handler=TwoPercentHandler, name="twopercent")
register_route('/<ngo_url>/doilasuta/succes', handler=DonationSucces, name="ngo-twopercent-success")


@app.route('/storage/<filename>', defaults={'folder': None})
@app.route('/storage/<folder>/<filename>')
def storage(folder, filename):
    # TODO Storage emulation for Development. To be superseded by S3.
    """
    Fake storage class
    :param folder:
    :param filename:
    :return:
    """
    if folder:
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename)
    else:
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename)
