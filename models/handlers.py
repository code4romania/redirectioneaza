
import os
import webapp2
import jinja2
import urlparse
import logging

from logging import info, warn

# globals
from appengine_config import *

# user object
from google.appengine.api import users, urlfetch
from google.appengine.api import mail
from google.appengine.ext import ndb

from webapp2_extras import sessions, auth, json

from models import NgoEntity, Donor
from email import EmailManager


def get_jinja_enviroment(account_view_folder=''):
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            + VIEWS_FOLDER
            + account_view_folder ),
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.i18n'],
        autoescape=True)
    
# default values for every template
template_settings = {
    "bower_components": DEV_DEPENDECIES_LOCATION,
    "DEV": DEV,
    "PRODUCTION": PRODUCTION,
    "title": TITLE,
    "contact_url": CONTACT_FORM_URL,
    "language": "ro",
    "base_url": "/",
    "months": MONTH_NAMES,
    "captcha_public_key": CAPTCHA_PUBLIC_KEY,
    "errors": None
}

class Handler(webapp2.RequestHandler):
    """this is just a wrapper over webapp2.RequestHandler"""
    pass

class BaseHandler(Handler):

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)


        self.template_values = {}
        self.template_values.update(template_settings)

        self.template_values["is_admin"] = users.is_current_user_admin()

        self.jinja_enviroment = get_jinja_enviroment()

        # Set webapp2.uri_for as global to be used in jinja2 templates
        self.jinja_enviroment.globals.update({
            'uri_for': webapp2.uri_for,
            # we need the DEV var everywhere in the site
            "DEV": DEV
        })

    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        if not DEV:
            host = self.request.host
            custom_subdomains = [
                'ikea.redirectioneaza.ro',
                'lidl.redirectioneaza.ro',
                'jysk.redirectioneaza.ro',
                'avon.redirectioneaza.ro'
            ]

            self.is_ikea_subdomain = host == custom_subdomains[0]
            self.is_lidl_subdomain = host == custom_subdomains[1]
            self.is_jysk_subdomain = host == custom_subdomains[2]
            self.is_avon_subdomain = host == custom_subdomains[3]

            self.template_values['custom_subdomain'] = host in custom_subdomains

        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        return self.session_store.get_session()

    # method used to set the
    def set_template(self, template):
        self.template = self.jinja_enviroment.get_template(template)

    def render(self, template_name=None):
        template = template_name if template_name is not None else self.template_name
        
        self.set_template( template )

        self.response.headers.update(HTTP_HEADERS)

        self.response.write(self.template.render(self.template_values))

    def return_json(self, obj={}, status_code=200):

        self.response.content_type = 'application/json'
        self.response.set_status(status_code)

        try:
            def json_serial(obj):
                """JSON serializer for objects not serializable by default json code"""

                if isinstance(obj, datetime) or isinstance(obj, date):
                    serial = obj.isoformat()
                    return serial
                else:
                    raise TypeError("Type not serializable")

            self.response.write( json.encode(obj, default=json_serial) )
        except Exception, e:
            warn(e)

            obj = {
                "error": "Error when trying to json encode the response"
            }
            self.response.write( json.encode(obj) )

    # USER METHODS
    def get_geoip_data(self, ip_address=None):

        headers = self.request.headers

        if not ip_address:
            ip_address = self.request.remote_addr

        # get the country from appengine
        # https://cloud.google.com/appengine/docs/standard/python/how-requests-are-handled#app-engine-specific-headers
        country = headers.get('X-AppEngine-Country', '')

        # if we have the country header, and it's different than ZZ (unknown)
        if country and country != 'ZZ':
            region = headers.get('X-AppEngine-Region', '')
            city = headers.get('X-AppEngine-City', '')
            lat_long = headers.get('X-AppEngine-CityLatLong', '')

            response =  {
                "country": country,
                "region": region,
                "city": city,
                "lat_long": lat_long,
                "ip_address": ip_address
            }
            return json.encode(response)

        # if we don't have that info, just return the ip_address
        return json.encode({"ip_address": ip_address})

    def get_ngo_and_donor(self, projection=True):

        ngo_id = str( self.request.route_kwargs.get("ngo_url") )
        donor_id = int( self.session.get("donor_id", 0) )

        if ngo_id and donor_id:
            list_of_entities = ndb.get_multi([
                ndb.Key("NgoEntity", ngo_id), 
                ndb.Key("Donor", donor_id)
            ])

            ngo = list_of_entities[0]
            donor = list_of_entities[1]
        
        else:
            ngo = ndb.Key("NgoEntity", ngo_id).get() if ngo_id else None

            donor = ndb.Key("Donor", donor_id).get() if donor_id else None

        # if DEV and not donor:
        #     donor = Donor(
        #         first_name = 'Prenume',
        #         last_name = 'Nume',
        #         city = 'Iasi',
        #         county = 'Iasi',
        #         email = 'email@code4.ro',
        #         tel = '0700000000',
        #         anonymous = False,
        #         geoip = '',
        #         ngo = ngo.key,
        #         pdf_url = 'https://media.giphy.com/media/Vuw9m5wXviFIQ/giphy.gif'
        #     )

        # if we didn't find the ngo or donor, raise
        if ngo is None:
            self.abort(404)

        # if it doesn't have a cookie, he must not be on the right page
        # redirect to the ngo's main page
        if donor_id is None:
            self.redirect( self.uri_for("ngo-url", ngo_url=ngo_id) )
            return False

        # if we didn't find the donor than the cookie must be wrong, unset it
        # and redirect to the ngo page
        if donor is None:
            if "donor_id" in self.session:
                self.session.pop("donor_id") 

            self.redirect( self.uri_for("ngo-url", ngo_url=ngo_id) )
            return False


        self.ngo = ngo
        self.donor = donor

        return True

    def send_email(self, email_type, user):

        if not user.email:
            return

        if email_type == "signup":
            subject = "Confirmare cont redirectioneaza.ro"

            user_id = user.get_id()
            token = self.user_model.create_signup_token(user_id)
            verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)

            html_template = self.jinja_enviroment.get_template("email/signup/signup_inline.html")
            txt_template = self.jinja_enviroment.get_template("email/signup/signup_text.txt")
        
            template_values = {
                "name": user.last_name,
                "contact_url": CONTACT_FORM_URL,
                "url": verification_url,
                "host": self.request.host
            }

        elif email_type == "reset-password":
            subject = "Resetare parola pentru contul redirectioneaza.ro"

            user_id = user.get_id()
            token = self.user_model.create_signup_token(user_id)
            verification_url = self.uri_for('verification', type='p', user_id=user_id, signup_token=token, _full=True)
            
            html_template = None # self.jinja_enviroment.get_template("email/reset/reset-password.html")
            txt_template = self.jinja_enviroment.get_template("email/reset/reset_password.txt")
            
            template_values = {
                "name": user.last_name,
                "contact_url": CONTACT_FORM_URL,
                "url": verification_url,
            }

        elif email_type == "twopercent-form":
            subject = "Formularul tau de redirectionare 2%"
            
            html_template = None # self.jinja_enviroment.get_template("email/twopercent-form/twopercent-form.html")
            txt_template = self.jinja_enviroment.get_template("email/twopercent-form/twopercent_form.txt")
            
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
                "name": "{0} {1}".format(user.first_name, user.last_name),
                "email": user.email
            }

            EmailManager.send_email(sender=sender, receiver=receiver, subject=subject, text_template=text_body, html_template=html_body)

        except Exception, e:

            warn(e)


def user_required(handler):
    """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        
        auth = self.auth
        if not auth.get_user_by_session() and not users.is_current_user_admin():
            self.redirect(self.uri_for('login'), abort=True)
        else:
            return handler(self, *args, **kwargs)

    return check_login

class AccountHandler(BaseHandler):
    """class used for logged in users"""

    @webapp2.cached_property
    def auth(self):
        """Shortcut to access the auth instance as a property."""
        return auth.get_auth() # request=self.request

    @webapp2.cached_property
    def user_info(self):
        """Shortcut to access a subset of the user attributes that are stored
            in the session (cookie).

            The list of attributes to store in the session is specified in
            config['webapp2_extras.auth']['user_attributes'].
            :returns
            A dictionary with most user information
        """
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        """Shortcut to access the user's ndb entity.
            It goes to the datastore.

            :returns
            The user's ndb entity
        """
        # it takes the user's info from the session cookie
        u = self.user_info
        # then using the ndb model queries the datastore
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        """Returns the implementation of the user model.

            It is consistent with config['webapp2_extras.auth']['user_model'], if set.
        """
        return self.auth.store.user_model

    @webapp2.cached_property
    def session(self):
        """override BaseHandler session method in order to use the datastore as the backend."""
        return self.session_store.get_session(backend="datastore")
