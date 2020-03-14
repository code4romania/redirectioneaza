# -*- coding: utf-8 -*-

from urlparse import urlparse

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from hashlib import sha1
from webapp2_extras import json, security

from appengine_config import LIST_OF_COUNTIES, USER_UPLOADS_FOLDER, USER_FORMS, ANAF_OFFICES

# also import captcha settings
from appengine_config import CAPTCHA_PRIVATE_KEY, CAPTCHA_POST_PARAM, DEFAULT_NGO_LOGO, DONATION_LIMIT

from models.handlers import BaseHandler
from models.models import NgoEntity, Donor
from models.storage import CloudStorage
from models.create_pdf import create_pdf

from captcha import submit

from logging import info
import re
import json
import datetime


"""
Handlers used for ngo 
"""
class NgoHandler(BaseHandler):
    def get(self, ngo_url):

        self.redirect( self.uri_for("twopercent", ngo_url=ngo_url) )


class TwoPercentHandler(BaseHandler):
    template_name = 'twopercent.html'

    def get(self, ngo_url):

        ngo = NgoEntity.get_by_id(ngo_url)
        # if we didn't find it or the ngo doesn't have an active page
        if ngo is None or ngo.active == False:
            self.error(404)
            return

        # if we still have a cookie from an old session, remove it
        if "donor_id" in self.session:
            self.session.pop("donor_id")

        if "has_cnp" in self.session:
            self.session.pop("has_cnp")
            # also we can use self.session.clear(), but it might delete the logged in user's session
        
        self.template_values["title"] = "Donatie 2%"
        # make sure the ngo shows a logo
        ngo.logo = ngo.logo if ngo.logo else DEFAULT_NGO_LOGO
        self.template_values["ngo"] = ngo
        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values['limit'] = DONATION_LIMIT
        
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
                    raise

            except Exception, e:

                self.template_values["ngo_website"] = None
        else:

            self.template_values["ngo_website"] = None    


        now = datetime.datetime.now()
        can_donate = not now.date() > DONATION_LIMIT

        self.template_values["can_donate"] = can_donate
        
        self.render()

    def post(self, ngo_url):

        post = self.request
        errors = {
            "fields": [],
            "server": False
        }

        self.ngo = NgoEntity.get_by_id(ngo_url)
        if self.ngo is None:
            self.error(404)
            return

        # if we have an ajax request, just return an answer
        self.is_ajax = self.request.get("ajax", False)

        def get_post_value(arg, add_to_error_list=True):
            value = post.get(arg)

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

        # if the user wants to redirect for 2 years
        two_years = post.get('two-years') == 'on'

        # if he would like the ngo to see the donation
        donor_dict['anonymous'] = post.get('anonim') != 'on'

        # what kind of income does he have: wage or other
        donor_dict['income'] = post.get('income', 'wage')

        # the ngo data
        ngo_data = {
            "name": self.ngo.name,
            "account": self.ngo.account.upper(),
            "cif": self.ngo.cif,
            "two_years": two_years,
            "special_status": self.ngo.special_status
        }
        
        if len(errors["fields"]):
            self.return_error(errors)
            return

        captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, self.request.remote_addr)

        # if the captcha is not valid return
        if not captcha_response.is_valid:
            
            errors["fields"].append("codul captcha")
            self.return_error(errors)
            return

        # the user's folder name, it's just his md5 hashed db id
        user_folder = security.hash_password('123', "md5")

        # a way to create unique file names
        # get the local time in iso format
        # run that through SHA1 hash
        # output a hex string
        filename = "{0}/{1}/{2}".format(USER_FORMS, str(user_folder), sha1( datetime.datetime.now().isoformat() ).hexdigest())

        pdf = create_pdf(donor_dict, ngo_data)

        file_url = CloudStorage.save_file(pdf, filename)

        # close the file after it has been uploaded
        pdf.close()

        # create the donor and save it
        donor = Donor(
            first_name = donor_dict["first_name"],
            last_name = donor_dict["last_name"],
            city = donor_dict["city"],
            county = donor_dict["county"],
            email = donor_dict['email'],
            tel = donor_dict['tel'],
            anonymous = donor_dict['anonymous'],
	    two_years = two_years,
            income = donor_dict['income'],
            # make a request to get geo ip data for this user
            geoip = self.get_geoip_data(),
            ngo = self.ngo.key,
            pdf_url = file_url
        )

        donor.put()

        # set the donor id in cookie
        self.session["donor_id"] = str(donor.key.id())
        self.session["has_cnp"] = bool(donor_dict["cnp"])

        # send and email to the donor with a link to the PDF file
        self.send_email("twopercent-form", donor)

        # if not an ajax request, redirect
        if self.is_ajax:
            
            self.response.set_status(200)
            
            response = {
                "url": self.uri_for("ngo-twopercent-success", ngo_url=ngo_url),
                "form_url": file_url
            }
            self.response.write(json.dumps(response))
        else:
            self.redirect( self.uri_for("ngo-twopercent-success", ngo_url=ngo_url) )

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
            self.template_values[ key ] = self.request.POST[ key ]

        # render a response
        self.render()

class DonationSucces(BaseHandler):
    template_name = 'succes.html'
    def get(self, ngo_url):

        if self.get_ngo_and_donor() is False:
            return

        self.template_values["ngo"] = self.ngo
        self.template_values["donor"] = self.donor
        self.template_values["title"] = "Donatie 2% - succes"
        self.template_values['limit'] = DONATION_LIMIT

        # county = self.donor.county.lower()
        # self.template_values["anaf"] = ANAF_OFFICES.get(county, None)

        # for now, disable showing the ANAF office
        self.template_values["anaf"] = None

        # if the user didn't provide a CNP show a message
        self.template_values["has_cnp"] = self.session.get("has_cnp", False)


        self.render()

    def post(self, ngo_url):
        # TODO: to be implemented
        post = self.request

        if self.get_ngo_and_donor() is False:
            return

        self.session.pop("donor_id")

        signed_pdf = post.get("signed-pdf")

        # TODO file upload
        
