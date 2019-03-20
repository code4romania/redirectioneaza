# -*- coding: utf-8 -*-
import datetime
import json
import re
from urllib.parse import urlparse

from flask import redirect, render_template, url_for, abort, request, session, jsonify

from config import CAPTCHA_PRIVATE_KEY, DEFAULT_NGO_LOGO
from config import LIST_OF_COUNTIES
from core import db
from models.create_pdf import create_pdf
from models.handlers import BaseHandler
from models.models import NgoEntity, Donor
from .captcha import submit

"""
Handlers used for ngo 
"""


class NgoHandler(BaseHandler):
    def get(self, ngo_url):

        return redirect(url_for("twopercent", ngo_url=ngo_url))


class TwoPercentHandler(BaseHandler):
    template_name = 'twopercent.html'

    def get(self, ngo_url):

        ngo = NgoEntity.query.filter_by(url=ngo_url).first()
        # if we didn't find it or the ngo doesn't have an active page
        if not ngo or not ngo.active:
            return abort(404)

        # if we still have a cookie from an old session, remove it
        if "donor_id" in session:
            session.pop("donor_id")

        if "has_cnp" in session:
            session.pop("has_cnp")

        self.template_values["title"] = "Donatie 2%"
        # make sure the ngo shows a logo
        ngo.logo = ngo.logo if ngo.logo else DEFAULT_NGO_LOGO
        self.template_values["ngo"] = ngo
        self.template_values["counties"] = LIST_OF_COUNTIES

        # the ngo website
        ngo_website = ngo.website if ngo.website else None
        if ngo_website:
            # try and parse the the url to see if it's valid
            try:
                url_dict = urlparse(ngo_website)

                if not url_dict.scheme:
                    url_dict = url_dict._replace(scheme='http')

                # if we have a netloc, than the url is valid
                # use the netloc as the website name
                if url_dict.netloc:

                    self.template_values["ngo_website_description"] = url_dict.netloc
                    self.template_values["ngo_website"] = url_dict.geturl()

                # of we don't have the netloc, when parsing the url
                # urlparse might send it to path
                # move that to netloc and remove the path
                elif url_dict.path:

                    url_dict = url_dict._replace(netloc=url_dict.path)
                    self.template_values["ngo_website_description"] = url_dict.path

                    url_dict = url_dict._replace(path='')

                    self.template_values["ngo_website"] = url_dict.geturl()
                else:
                    raise Exception("Runtime error")

            except Exception as e:

                self.template_values["ngo_website"] = None
        else:

            self.template_values["ngo_website"] = None

        now = datetime.datetime.now()
        can_donate = True
        # if now.month > 3 or (now.month == 3 and now.day > 15):
        #     can_donate = False

        self.template_values["can_donate"] = can_donate

        return render_template(self.template_name, **self.template_values)

    def post(self, ngo_url):

        errors = {
            "fields": [],
            "server": False
        }

        self.ngo = NgoEntity.query.filter_by(url=ngo_url).first()
        if not self.ngo:
            return abort(404)

        # if we have an ajax request, just return an answer
        self.is_ajax = request.form.get("ajax", False)

        def get_post_value(arg, add_to_error_list=True):
            value = request.form.get(arg)

            # if we received a value
            if value:

                # it should only contains alpha numeric, spaces and dash
                if re.match(r'^[\w\s.\-ăîâșț]+$', value, flags=re.I | re.UNICODE) is not None:

                    # additional validation
                    if arg == "cnp" and len(value) != 13:
                        errors["fields"].append(arg)
                        return ""

                    return value

                # the email has the @ so the first regex will fail
                elif arg == 'email':

                    # if we found a match
                    if re.match(r'[^@]+@[^@]+\.[^@]+', value) is not None:
                        return value

                    errors["fields"].append(arg)
                    return ''

                else:

                    errors["fields"].append(arg)

            elif add_to_error_list:
                errors["fields"].append(arg)

            return ""

        donor_dict = {}

        # the donor's data
        donor_dict["first_name"] = get_post_value("nume").title()
        donor_dict["last_name"] = get_post_value("prenume").title()
        donor_dict["father"] = get_post_value("tatal").title()
        donor_dict["cnp"] = get_post_value("cnp", False)

        donor_dict["email"] = get_post_value("email").lower()
        donor_dict["tel"] = get_post_value("tel", False)

        donor_dict["street"] = get_post_value("strada").title()
        donor_dict["number"] = get_post_value("numar", False)

        # optional data
        donor_dict["bl"] = get_post_value("bloc", False)
        donor_dict["sc"] = get_post_value("scara", False)
        donor_dict["et"] = get_post_value("etaj", False)
        donor_dict["ap"] = get_post_value("ap", False)

        donor_dict["city"] = get_post_value("localitate").title()
        donor_dict["county"] = get_post_value("judet")

        # if he would like the ngo to see the donation
        donor_dict['anonymous'] = request.form.get('anonim') != 'on'

        donor_dict['income'] = request.form.get('income', 'wage')

        # the ngo data
        ngo_data = {
            "name": self.ngo.name,
            "account": self.ngo.account.upper(),
            "cif": self.ngo.cif,
            "special_status": self.ngo.special_status
        }

        if len(errors["fields"]):
            self.return_error(errors)
            return

        captcha_response = submit(request.form.get('g-recaptcha-response'), CAPTCHA_PRIVATE_KEY, request.remote_addr)

        # if the captcha is not valid return
        if not captcha_response.is_valid:
            errors["fields"].append("codul captcha")
            self.return_error(errors)
            return

        file_url = create_pdf(donor_dict, ngo_data)

        # create the donor and save it
        donor = Donor(
            first_name=donor_dict["first_name"],
            last_name=donor_dict["last_name"],
            city=donor_dict["city"],
            county=donor_dict["county"],
            email=donor_dict['email'],
            tel=donor_dict['tel'],
            anonymous=donor_dict['anonymous'],
            income=donor_dict['income'],
            # make a request to get geo ip data for this user
            geoip=self.get_geoip_data(),
            ngo=self.ngo,
            pdf_url=file_url
        )

        db.session.add(donor)

        db.session.commit()

        # set the donor id in cookie
        session["donor_id"] = str(donor.id)
        session["has_cnp"] = bool(donor_dict["cnp"])

        # send and email to the donor with a link to the PDF file
        self.send_email("twopercent-form", donor)

        # if not an ajax request, redirect
        if self.is_ajax:
            response = {
                "url": url_for("ngo-twopercent-success", ngo_url=ngo_url),
                "form_url": file_url
            }
            return jsonify(response), 200
        else:
            return redirect(url_for(
                "ngo-twopercent-success", ngo_url=ngo_url))

    def return_error(self, errors):

        if self.is_ajax:
            self.response.set_status(400)
            self.response.write(json.dumps(errors))

            return

        self.template_values["title"] = "Donatie 2%"
        self.template_values["ngo"] = self.ngo

        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values["errors"] = errors

        for key in self.request.POST:
            self.template_values[key] = request.form[key]

        # render a response
        return render_template(self.template_name, **self.template_values)


class DonationSucces(BaseHandler):
    template_name = 'succes.html'

    def get(self, ngo_url):
        # if self.get_ngo_and_donor() is False:
        #     return

        self.template_values["ngo"] = NgoEntity.query.filter_by(url=ngo_url).first()
        self.template_values["donor"] = Donor.query.filter_by(id=session['donor_id']).first()
        self.template_values["title"] = "Donatie 2% - succes"

        # county = self.donor.county.lower()
        # self.template_values["anaf"] = ANAF_OFFICES.get(county, None)

        # for now, disable showing the ANAF office
        self.template_values["anaf"] = None

        # if the user didn't provide a CNP show a message
        self.template_values["has_cnp"] = session["has_cnp"] or False

        return render_template(self.template_name, **self.template_values)

    def post(self, ngo_url):
        # Find out what what this supposed to be
        # TODO: to be implemented

        if self.get_ngo_and_donor() is False:
            return

        session.pop("donor_id")

        signed_pdf = request.form.get("signed-pdf")

        # TODO file upload
