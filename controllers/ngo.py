# -*- coding: utf-8 -*-

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from appengine_config import SECRET_KEY, AWS_PDF_URL, LIST_OF_COUNTIES

from models.handlers import BaseHandler
from models.models import NgoEntity, Donor


from logging import info
import re
ngo = {
    "logo": "http://images.clipartpanda.com/spinner-clipart-9cz75npcE.jpeg",
    "name": "Nume asoc",
    "description": "o descriere lunga",
    "ngo": {}
}
ngo["key"] = {
    "id": lambda: "sss"
}


"""
Handlers used for ngo 
"""
class NgoHandler(BaseHandler):
    def get(self, ngo_url):

        self.redirect( ngo_url + "/doilasuta" )


class TwoPercentHandler(BaseHandler):
    template_name = 'twopercent.html'

    def get(self, ngo_url):

        
        # ngo = NgoEntity.get_by_id(ngo_url)
        # if ngo is None:
            # self.error(404)
            # return


        self.set_template( self.template_name )
        
        self.template_values["title"] = "Donatie 2%"
        self.template_values["ngo"] = ngo
        self.template_values["counties"] = LIST_OF_COUNTIES
        
        self.render()

    def post(self, ngo_url):

        post = self.request
        errors = {
            "fields": [],
            "server": False
        }

        # ngo = NgoEntity.get_by_id(ngo_url)
        # if ngo is None:
            # self.error(404)
            # return
        self.ngo = ngo

        def get_post_value(arg, add_to_error_list=True):
            # if we received an value and it only contains alpha numeric, spaces and dash
            if post.get(arg):
                if re.match('^[\w\s-]+$', post.get(arg)) is not None:
                    return post.get(arg)
                else:
                    errors["fields"].append(arg)
            
            elif add_to_error_list:
                errors["fields"].append(arg)

            return None

        payload = {}

        # the person's data
        payload["first_name"] = get_post_value("nume")
        payload["last_name"] = get_post_value("prenume")
        payload["father"] = get_post_value("tatal")
        payload["cnp"] = get_post_value("cnp")

        payload["street"] = get_post_value("strada")
        payload["number"] = get_post_value("numar")

        # optional data
        payload["bl"] = get_post_value("bloc", False)
        payload["sc"] = get_post_value("scara", False)
        payload["et"] = get_post_value("etaj", False)
        payload["ap"] = get_post_value("ap", False)

        payload["city"] = get_post_value("localitate")
        payload["county"] = get_post_value("judet")

        # the ngo data
        # payload["name"] = self.ngo.name
        # payload["account"] = self.ngo.account
        # payload["cif"] = self.ngo.cif

        payload["secret_key"] = SECRET_KEY
        
        if len(errors["fields"]):
            self.return_error(errors)
            return


        # send to aws and get the pdf url
        aws_rpc = urlfetch.create_rpc()
        info(AWS_PDF_URL)
        urlfetch.make_fetch_call(aws_rpc, AWS_PDF_URL, payload=payload, method="POST")

        # save to DB while we wait for aws
        person = Donor(
            first_name = post.get("first_name"),
            last_name = post.get("last_name"),
            city = post.get("city"),
            county = post.get("county"),
            # make a request to get geo ip data for this user
            geoip = self.get_geoip_data(),
            # ngo = self.ngo.key
        )

        # The returned data structure has the following fields:
        #   status_code:    HTTP status code returned by the server 
        #   content:        string containing the response from the server 
        #   headers:        dictionary of headers returned by the server
        result = aws_rpc.get_result()
        if result.status_code == 200:
            content = json.loads(result.content)
            person.pdf_url = content.url

            person.put()
        else:
            errors["server"] = True

            self.return_error(errors)
            return

        # set the donor id in cookie
        self.response.set_cookie("donor_id", str(person.key.id()), max_age=2592000, path='/')

        self.redirect( ngo_url + "/doilasuta/pas-2" )

    def return_error(self, errors):
        self.set_template( self.template_name )

        self.template_values["title"] = "Donatie 2%"
        self.template_values["ngo"] = self.ngo
        
        self.template_values["counties"] = LIST_OF_COUNTIES
        self.template_values["errors"] = errors
        
        for key in self.request.POST:
            self.template_values[ key ] = self.request.POST[ key ]

        # render a response
        self.render()

class TwoPercent2Handler(BaseHandler):
    def get(self, ngo_url):
        post = self.request

        self.get_ngo_and_donor()

        # set the index template
        self.set_template('twopercent-2.html')
        self.template_values["ngo"] = ngo
        
        # render a response
        self.render()




class DonationSucces(BaseHandler):
    def get(self, ngo_url):

        self.get_ngo_and_donor()

        # unset the cookie if the ngo does not allow file upload
        # otherwise we still need it
        if self.ngo.allow_upload:
            self.response.delete_cookie("donor_id", path='/')

    def post(self, ngo_url):
        post = self.request

        self.get_ngo_and_donor()

