
import os
import webapp2
import jinja2
import urlparse
import logging
import json

from logging import info

# globals
from appengine_config import *

# user object
from google.appengine.api import users, urlfetch
from google.appengine.api import mail
from google.appengine.ext import ndb

from webapp2_extras import sessions, auth

from models import NgoEntity, Donor


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
    "title": TITLE,
    "contact_url": CONTACT_FORM_URL,
    "language": "ro",
    "base_url": "/"
}

class Handler(webapp2.RequestHandler):
    """this is just a wrapper over webapp2.RequestHandler"""
    pass

class BaseHandler(Handler):

    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)

        self.template_values = template_settings
        self.jinja_enviroment = get_jinja_enviroment()

    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
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

        self.response.write(self.template.render(self.template_values))

    # USER METHODS
    def get_geoip_data(self, ip_address=None):
        if not ip_address:
            ip_address = self.request.remote_addr
        
        if DEV:
            return json.dumps({"ip_address": ip_address})    

        # set the default value to 10 seconds
        deadline = 10
        resp = urlfetch.fetch(url=GEOIP_SERVICES[0].format(ip_address), deadline=deadline)

        geoip_response = json.loads(resp.content)

        # check to see if it was a success
        if geoip_response["status"] == "success":

            return resp.content
        
        # if we surpassed the quota, try the other service
        else:
            # call the second service
            resp = urlfetch.fetch(url=GEOIP_SERVICES[1].format(ip_address), deadline=deadline)

            # just to make sure we don't get an over quota, or IP not found
            if str(resp.status_code) not in ["403", "404"]:
                
                return resp.content
            else:
                # if this one fails alos return empty dict
                return json.dumps({"ip_address": ip_address})

    def get_ngo_and_donor(self):

        ngo_id = str( self.request.route_kwargs.get("ngo_url") )
        donor_id = int( self.session.get("donor_id", 1) )

        list_of_entities = ndb.get_multi([
            ndb.Key("NgoEntity", ngo_id), 
            ndb.Key("Donor", donor_id)
        ])

        ngo = list_of_entities[0]
        donor = list_of_entities[1]

        # if we didn't find the ngo or donor, raise
        if ngo is None:
            webapp2.abort(404)

        # if it doesn't have a cookie, he must not be on the right page
        # redirect to the ngo's main page
        if donor_id is None:
            self.redirect("/" + ngo_id)

        # if we didn't find the donor than the cookie must be wrong, unset it
        # and redirect to the ngo page
        if donor is None:
            if "donor_id" in self.session:
                self.session.pop("donor_id") 
            
            self.redirect("/" + ngo_id)


        self.ngo = ngo
        self.donor = donor

def user_required(handler):
    """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
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


    def send_email(self, email_type, user):
        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)

        sender_address = CONTACT_EMAIL_ADDRESS
        user_address = user.email

        if email_type == "signup":
            subject = "Confirmare cont donezsi.eu"
            verification_url = self.uri_for('verification', type='v', user_id=user_id, signup_token=token, _full=True)

            template = self.jinja_enviroment.get_template("email/signup/signup_inline.html")

        elif email_type == "reset-password":
            subject = "Resetare parola pentru contul donezsi.eu"
            verification_url = self.uri_for('verification', type='p', user_id=user_id, signup_token=token, _full=True)
            
            template = self.jinja_enviroment.get_template("email/reset-password.html")

        else:
            return
        
        body = template.render({
            "name": user.first_name,
            "email": user_address,
            "contact_url": CONTACT_FORM_URL,
            "url": verification_url
        })

        mail.send_mail(sender_address, user_address, subject, body)
        info(body)