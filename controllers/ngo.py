# -*- coding: utf-8 -*-

from google.appengine.api import urlfetch

from appengine_config import SECRET_KEY, AWS_PDF_URL, GEOIP_URL

from models.handlers import BaseHandler
from models.models import NgoEntity


"""
Handlers used for ngo 
"""
class NgoHandler(BaseHandler):
    def get(self, ngo_url):

        self.redirect( ngo_url + "/doilasuta" )


class TwoPercentHandler(BaseHandler):
    def get(self, ngo_url):

        ngo = NgoEntity.get_by_id(ngo_url)
        
        if ngo is None:
            self.error(404)
            return

        # set the index template
        self.set_template('twopercent.html')

        
        # render a response
        self.render()

    def post(self):

        post = self.request

        # validation


        payload = {}

        payload["secret_key"] = SECRET_KEY
        
        # send to aws and get the pdf url
        aws_rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(aws_rpc, AWS_PDF_URL, payload=payload, method="POST")

        # save to DB while we wait for aws
        person = Donor(
            first_name = post.get("first_name"),
            last_name = post.get("last_name"),
            city = post.get("city"),
            county = post.get("county"),
            # make a request to get geo ip data for this user
            geoip = self.get_geoip_data(),
            ngo = ngo.key
        )

        # The returned data structure has the following fields:
        #   status_code:    HTTP status code returned by the server 
        #   content:        string containing the response from the server 
        #   headers:        dictionary of headers returned by the server
        result = aws_rpc.get_result()
        if result.status_code == 200:
            text = result.content

class TwoPercent2Handler(BaseHandler):
    def get(self, ngo_url):

        ngo = NgoEntity.get_by_id(ngo_url)
        
        if ngo is None:
            self.error(404)
            return



        # set the index template
        self.set_template('twopercent.html')

        
        # render a response
        self.render()

    def post(self):

        post = self.request


class DonationSucces(BaseHandler):
    def get(self, ngo_url, donor_id):
        ngo = NgoEntity.get_by_id(ngo_url)

        if ngo is None:
            self.error(404)
            return

        donor = Donor.get_by_id(int(donor_id))
        
        if donor_id is None:
            self.error(404)
            return

        