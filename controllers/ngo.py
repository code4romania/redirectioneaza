# -*- coding: utf-8 -*-


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



        