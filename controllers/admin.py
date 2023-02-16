
from copy import deepcopy
from logging import error
from operator import itemgetter
from datetime import datetime

from google.appengine.api import users, mail
from google.appengine.ext import ndb

from models.handlers import BaseHandler
from my_account import NgoDetailsHandler

from models.models import NgoEntity, Donor
from models.user import User

from appengine_config import LIST_OF_COUNTIES, START_YEAR

# dict used as cache
stats_dict = {
    "init": False,
    "ngos": 0,
    "forms": 0,
    "years": {},
    "counties": {}
}

"""
Handlers  for admin routing
"""
class AdminHome(BaseHandler):
    template_name = 'admin/index.html'
    def get(self):

        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))

        self.template_values["title"] = "Admin"
        now = datetime.now()

        ngos = []
        donations = []
        from_date = datetime(now.year, 1, 1, 0, 0)

        # if we don't have any data
        if stats_dict["init"] == False:
            try:
                projection = [NgoEntity.county, NgoEntity.date_created]
                # ngos = NgoEntity.query(NgoEntity.date_created < from_date).fetch(projection=projection)
                ngos = []
            except Exception as e:
                error(e)
                ngos = NgoEntity.query(NgoEntity.date_created < from_date).fetch()

            # donations = Donor.query(Donor.date_created < from_date).fetch(projection=[Donor.date_created, Donor.county])
            donations = []

            stats_dict['ngos'] = len(ngos)
            stats_dict['forms'] = len(donations)

            # init the rest of the dict
            for x in xrange(START_YEAR, now.year + 1):
                stats_dict["years"][x] = {
                    "ngos": 0,
                    "forms": 0,
                }

            counties = LIST_OF_COUNTIES + ['1', '2', '3', '4', '5', '6', 'RO']

            for county in counties:
                stats_dict["counties"][county] = {
                    "ngos": 0,
                    "forms": 0,
                }

            self.add_data(stats_dict, ngos, donations)

            stats_dict["init"] = True


        # just look at the last year
        ngos = NgoEntity.query(NgoEntity.date_created >= from_date).fetch(projection=[NgoEntity.county, NgoEntity.date_created])
        donations = Donor.query(Donor.date_created >= from_date).fetch(projection=[Donor.date_created, Donor.county])

        stats = deepcopy(stats_dict)
        stats['ngos'] = len(ngos) + stats_dict['ngos']
        stats['forms'] = len(donations) + stats_dict['forms']

        self.add_data(stats, ngos, donations)

        self.template_values["stats_dict"] = stats

        # render a response
        self.render()

    def add_data(self, obj, ngos, donations):
        for ngo in ngos:
            if ngo.date_created.year in obj["years"]:
                obj["years"][ngo.date_created.year]['ngos'] += 1

            if ngo.county:
                obj["counties"][ngo.county]['ngos'] += 1

        for donation in donations:
            if donation.date_created.year in obj["years"]:
                obj["years"][donation.date_created.year]['forms'] += 1

            obj["counties"][donation.county]['forms'] += 1

class AdminNgosList(BaseHandler):
    template_name = 'admin/ngos.html'
    def get(self):

        if users.is_current_user_admin():
            user = users.get_current_user()
        else:
            self.redirect(users.create_login_url("/admin"))

        self.template_values["title"] = "Admin"

        try:
            projection = [NgoEntity.name, NgoEntity.county, NgoEntity.verified, NgoEntity.email]
            ngos = NgoEntity.query().fetch(projection=projection)
        except Exception as e:
            ngos = NgoEntity.query().fetch()

        # for ngo in ngos:
        #     ngo.number_of_donations = Donor.query(Donor.ngo == ngo.key).count()
        #     ngo.account_attached = User.query(User.ngo == ngo.key).count(1) == 1

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

        all_users = User.query().fetch()

        # make all the users a dict so we can sort them
        b = []
        for a in all_users:
            b.append(a.to_dict())

        all_users = sorted(b, key=itemgetter("created"), reverse=True)
        self.template_values["users"] = all_users

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
        
        self.template_values["owner"] = User.query(User.ngo == ngo.key).get()
        
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