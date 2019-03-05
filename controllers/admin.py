from flask_login import current_user
from flask import url_for, redirect, abort, render_template, request
from sqlalchemy import func
from models.user import User
from core import db, app
from utils import obj2dict

# from google.appengine.api import users, mail
# from google.appengine.ext import ndb
# from operator import itemgetter

from models.handlers import BaseHandler
from models.models import NgoEntity, Donor
from models.user import User
from appengine_config import LIST_OF_COUNTIES

"""
Handlers  for admin routing
"""


class AdminHandler(BaseHandler):
    template_name = 'admin/index.html'

    def get(self):

        if not current_user.is_admin:
            return redirect(url_for("/admin"))

        self.template_values["title"] = "Admin"

        ngos = NgoEntity.query.all()

        # TODO LOOK INTO HOW TO COMBINE HYBRID PROPERTIES WITH WITH_ENTITIES (PROJECTIONS)
        # .with_entities(NgoEntity.name,\
        #                                      NgoEntity.county,\
        #                                      NgoEntity.verified,\
        #                                      NgoEntity.email
        #                                      ).all()

        self.template_values["ngos"] = ngos

        # render a response
        return render_template(self.template_name, **self.template_values)


class UserAccounts(BaseHandler):
    template_name = 'admin/accounts.html'

    def get(self):
        if not current_user.is_admin:
            return redirect(url_for("admin"))

        all_users = User.query.all()

        self.template_values["users"] = all_users

        return render_template(self.template_name, **self.template_values)


class AdminNewNgoHandler(BaseHandler):
    template_name = 'admin/ngo.html'

    def get(self):

        if not current_user.is_admin:
            return redirect(url_for("admin"))

        # url_for("api-ngo-upload-url")
        self.template_values["ngo_upload_url"] = ''
        self.template_values["check_ngo_url"] = ''  # "/api/ngo/check-url/"
        self.template_values["counties"] = LIST_OF_COUNTIES

        self.template_values["ngo"] = {}

        # render a response
        return render_template(self.template_name, **self.template_values)


class AdminNgoHandler(BaseHandler):
    template_name = 'admin/ngo.html'

    def get(self, ngo_url):

        if not current_user.is_admin:
            return redirect(url_for("admin"))

        ngo = NgoEntity.query.filter_by(url=ngo_url).first()

        if not ngo:
            return abort(404)

        # url_for("api-ngo-upload-url")
        self.template_values["ngo_upload_url"] = ''
        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values["ngo"] = ngo

        self.template_values["other_emails"] = ', '.join(
            str(x) for x in ngo.other_emails) if ngo.other_emails else ""

        # render a response
        return render_template(self.template_name, **self.template_values)


class SendCampaign(BaseHandler):
    template_name = 'admin/campaign.html'

    def get(self):
        if not current_user.is_admin:
            return redirect(url_for("/admin"))

        return render_template(self.template_name, **self.template_values)

    def post(self):

        if not current_user.is_admin:
            return abort(400)

        subject = request.form.get('subiect')
        emails = [s.strip() for s in request.form.get('emails', "").split(",")]

        if not subject or not emails:
            return abort(500)

        sender_address = "Andrei Onel <contact@donezsi.eu>"

        html_template = app.jinja_env.get_template(
            "email/campaigns/first/index-inline.html")
        txt_template = app.jinja_env.get_template(
            "email/campaigns/first/index-text.txt")

        template_values = {}

        html_body = html_template.render(template_values)
        body = txt_template.render(template_values)

        for email in emails:
            user_address = email
            # TODO FIX MAIL SENDING
            #mail.send_mail(sender=sender_address, to=user_address, subject=subject, html=html_body, body=body)

        return redirect(url_for("admin-campanii"))
