from logging import info

from flask import url_for, redirect, abort, render_template, request
from flask_login import current_user
from flask_mail import Message

from redirectioneaza import app, mail
from redirectioneaza.config import DEV
from redirectioneaza.contact_data import LIST_OF_COUNTIES
from redirectioneaza.handlers.base import BaseHandler
from redirectioneaza.models import NgoEntity, User

"""
Handlers  for admin routing
"""


# TODO Revamp this with a real admin-only interface using Flask-Admin


class AdminHandler(BaseHandler):
    template_name = 'admin/index.html'

    def get(self):

        if not current_user.is_authenticated:
            return redirect(url_for('login'))

        if not current_user.is_admin:
            return redirect(url_for('index'))

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

        self.template_values["ngo_upload_url"] = url_for("api-ngo-upload-url")
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

            # TODO: This an actual email to be sent
            msg = Message(sender=sender_address, recipients=[user_address], subject=subject, html=html_body, body=body)

            if not DEV:
                mail.send(msg)
            else:
                info(msg)

        return redirect(url_for("admin-campanii"))
