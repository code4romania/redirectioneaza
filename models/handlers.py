
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
from webapp2_extras import sessions

from users import geoip_services


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
            "DEV": PRODUCTION,
            "title": TITLE,
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

    def render(self):
        self.response.write(self.template.render(self.template_values))

    # USER METHODS
    def get_geoip_data(self, ip_address):
        
        country = ""
        resp = urlfetch.fetch(url=geoip_services[0].format(ip_address))

        geoip_response = json.loads(resp.content)

        # check to see if it was a success
        if geoip_response["status"] == "success":

            country = geoip_response["countryCode"]
            geoip_response = json.dumps(resp.content)
        else:

            # if we surpassed the quota, try the other service
            # call the second service
            resp = urlfetch.fetch(url=geoip_services[1].format(ip_address))

            # just to make sure we don't get an over quota, or IP not found
            if str(resp.status_code) not in ["403", "404"]:
                
                # load the json just to read the country code
                geoip_response = json.loads(resp.content)
                country = geoip_response["country_code"]
                geoip_response = json.dumps(resp.content)

            else:
                geoip_response = json.dumps({})

        return geoip_response, country
