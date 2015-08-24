
from google.appengine.api import users
from google.appengine.ext import ndb

from models.handlers import BaseHandler
from my_account import NgoDetailsHandler

from models.models import NgoEntity, Donor

from appengine_config import AWS_PDF_URL, LIST_OF_COUNTIES

"""
Handlers  for admin routing
"""
class AdminHandler(BaseHandler):
    template_name = 'admin/index.html'
    def get(self):

        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))

        self.template_values["title"] = "Admin"

        try:
            projection = [NgoEntity.name, NgoEntity.county, NgoEntity.verified]
            ngos = NgoEntity.query().fetch(30, projection=projection)
        except Exception, e:
            ngos = NgoEntity.query().fetch(30)

        for ngo in ngos:
            ngo.number_of_donations = Donor.query(Donor.ngo == ngo.key).count()

        # sort them by no. of donations
        self.template_values["ngos"] = ngos # sorted(ngos, key=itemgetter('number_of_donations'), reverse=True)

        # render a response
        self.render()

class AdminNewNgoHandler(BaseHandler):
    template_name = 'admin/ngo.html'
    def get(self):
        
        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))


        self.template_values["AWS_SERVER_URL"] = AWS_PDF_URL + "/upload-file"
        self.template_values["check_ngo_url"] = "/api/check-ngo-api/"
        self.template_values["counties"] = LIST_OF_COUNTIES
        
        self.template_values["ngo"] = {}

        # render a response
        self.render()


class AdminNgoHandler(NgoDetailsHandler):
    template_name = 'admin/ngo.html'
    def get(self, ngo_url):
        
        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))

        ngo = NgoEntity.get_by_id(ngo_url)
        if ngo is None:
            self.error(404)
            return

        self.template_values["AWS_SERVER_URL"] = AWS_PDF_URL + "/upload-file"
        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values["ngo"] = ngo

        # render a response
        self.render()
