# import webapp2

from collections import namedtuple
from logging import warning

from flask import request, session, redirect, abort, url_for
from flask.views import MethodView
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer

# globals
from config import *
from core import app
from .email import EmailManager
from .models import NgoEntity, Donor

app.jinja_env.add_extension('jinja2.ext.autoescape')
app.jinja_env.add_extension('jinja2.ext.i18n')

# def get_jinja_enviroment(account_view_folder=''):
#     return jinja2.Environment(
#         loader=jinja2.FileSystemLoader(
#             os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
#             + VIEWS_FOLDER
#             + account_view_folder ),
#         extensions=['jinja2.ext.autoescape', 'jinja2.ext.i18n'],
#         autoescape=True)

# default values for every template

template_settings = {
    "bower_components": DEV_DEPENDECIES_LOCATION,
    "DEV": DEV,
    "PRODUCTION": PRODUCTION,
    "title": TITLE,
    "contact_url": CONTACT_FORM_URL,
    "language": "ro",
    "base_url": "/",
    "captcha_public_key": CAPTCHA_PUBLIC_KEY,
    "errors": None
}

app.jinja_env.globals = {**app.jinja_env.globals, **template_settings}


class Handler(MethodView):
    """this is just a wrapper over Flask MethodView"""
    pass


TokenValidationResponse = namedtuple('TokenValidationResponse', ['token_id', 'result', 'email', 'type'])


class BaseHandler(Handler):

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)

        self.template_values = {"is_admin": current_user.is_admin if current_user.is_authenticated else False}

        # TODO check where template_settings was loaded into template values
        # self.template_values.update(template_settings)

    # USER METHODS

    def generate_confirmation_token(self, email, token_type):

        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps({'email': email, 'type': token_type}, salt=app.config['SECURITY_PASSWORD_SALT'])

    def confirm_token(self, token, expiration=3600):

        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

        try:
            result = serializer.loads(
                token,
                salt=app.config['SECURITY_PASSWORD_SALT'],
                max_age=expiration
            )
        except Exception as e:
            return TokenValidationResponse(token_id=token, result=False, email=None, type=None)

        if not (isinstance(result, dict) and ('email' in result.keys() and 'type' in result.keys())):
            return TokenValidationResponse(token_id=token, result=False, email=None, type=None)

        if not ('p' == result['type'] or 'v' == result['type']):
            return TokenValidationResponse(token_id=token, result=False, email=None, type=None)

        return TokenValidationResponse(token_id=token, result=True, email=result['email'], type=result['type'])

    def get_geoip_data(self, ip_address=None):

        if not ip_address:
            ip_address = request.remote_addr

        # TODO - Country was GAE-specific header. Find out what else it was used for.

        return ip_address

    def get_ngo_and_donor(self, projection=True):

        # TODO - Find out why would one use projection here

        ngo_id = str(request.args.get("ngo_url"))

        donor_id = int(session["donor_id"] or 0)

        ngo = NgoEntity.query.filter_by(url=ngo_id)

        donor = Donor.query.filter_by(donor_email=donor_id)

        # if we didn't find the ngo or donor, raise
        if not ngo:
            return abort(404)

        # if it doesn't have a cookie, he must not be on the right page
        # redirect to the ngo's main page
        if not donor_id:
            return redirect(url_for("ngo-url", ngo_url=ngo_id))

        # if we didn't find the donor than the cookie must be wrong, unset it
        # and redirect to the ngo page
        if donor is None:
            if "donor_id" in session:
                session.pop("donor_id")

            return redirect(url_for("ngo-url", ngo_url=ngo_id))

        self.ngo = ngo
        self.donor = donor

        return True

    def send_email(self, email_type, user):

        if not user.email:
            return

        if email_type == "signup":
            subject = "Confirmare cont redirectioneaza.ro"

            token = self.generate_confirmation_token(user.email, 'v')
            # TODO Fix this
            verification_url = url_for('verification', token=token)

            html_template = app.jinja_env.get_template("email/signup/signup_inline.html")
            txt_template = app.jinja_env.get_template("email/signup/signup_text.txt")

            template_values = {
                "name": user.last_name,
                "contact_url": CONTACT_FORM_URL,
                "url": verification_url,
                "host": request.remote_addr
            }

        elif email_type == "reset-password":
            subject = "Resetare parola pentru contul redirectioneaza.ro"

            token = self.generate_confirmation_token(user.email, 'p')
            # TODO Fix this
            verification_url = url_for('verification', token=token)

            html_template = None
            txt_template = app.jinja_env.get_template("email/reset/reset_password.txt")

            template_values = {
                "name": user.last_name,
                "contact_url": CONTACT_FORM_URL,
                "url": verification_url,
            }

        elif email_type == "twopercent-form":
            subject = "Formularul tau de redirectionare 2%"

            html_template = None
            txt_template = app.jinja_env.get_template("email/twopercent-form/twopercent_form.txt")

            template_values = {
                "name": user.last_name,
                "form_url": user.pdf_url,
                "contact_url": CONTACT_FORM_URL
            }
        else:
            return

        try:

            text_body = txt_template.render(template_values) if txt_template else None
            html_body = html_template.render(template_values) if html_template else None

            sender = {
                "name": "redirectioneaza",
                "email": CONTACT_EMAIL_ADDRESS
            }
            receiver = {
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email
            }

            EmailManager.send_email(sender=sender, receiver=receiver, subject=subject,
                                    text_template=text_body, html_template=html_body)

        except Exception as e:

            warning(e)
