
from google.appengine.api import users, mail
from google.appengine.ext import ndb

from models.handlers import BaseHandler
from my_account import NgoDetailsHandler

from models.models import NgoEntity, Donor
from models.user import User

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
            ngo.account_attached = User.query(User.ngo == ngo.key).count(1) == 1

        # sort them by no. of donations
        self.template_values["ngos"] = ngos # sorted(ngos, key=itemgetter('number_of_donations'), reverse=True)

        # render a response
        self.render()


class UserAccounts(BaseHandler):
    template_name = 'admin/accounts.html'
    def get(self):
        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))

        self.template_values["users"] = User.query().fetch()

        self.render()


class AdminNewNgoHandler(BaseHandler):
    template_name = 'admin/ngo.html'
    def get(self):
        
        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))


        self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")
        self.template_values["check_ngo_url"] = "/api/ngo/check-url/"
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

        self.template_values["ngo_upload_url"] = self.uri_for("api-ngo-upload-url")
        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values["ngo"] = ngo
        
        self.template_values["other_emails"] = ', '.join(str(x) for x in ngo.other_emails) if ngo.other_emails else ""

        # render a response
        self.render()

class SendCampaign(NgoDetailsHandler):
    template_name = 'admin/campaign.html'
    def get(self):
        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))

        self.render()


    def post(self):
        
        if not users.is_current_user_admin():
            self.abort(400)

        subject = self.request.get('subiect')
        emails = [s.strip() for s in self.request.get('emails', "").split(",")]

        if not subject or not emails:
            self.abort(400)

        sender_address = "Andrei Onel <contact@donezsi.eu>"

        html_template = self.jinja_enviroment.get_template("email/campaigns/first/index-inline.html")
        txt_template = self.jinja_enviroment.get_template("email/campaigns/first/index-text.txt")

        template_values = {}

        html_body = html_template.render(template_values)
        body = txt_template.render(template_values)

        for email in emails:
            user_address = email
            mail.send_mail(sender=sender_address, to=user_address, subject=subject, html=html_body, body=body)
        
        self.redirect(self.uri_for("admin-campanii"))