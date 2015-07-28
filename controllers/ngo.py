# -*- coding: utf-8 -*-


from models.handlers import BaseHandler



"""
Handlers used for ngo 
"""
class NgoHandler(BaseHandler):
    def get(self, ngo_url):

        # set the index template
        self.set_template('index.html')

        
        # render a response
        self.render()


class TwoPercentHandler(BaseHandler):
    def get(self, ngo_url):

        # set the index template
        self.set_template('twopercent.html')

        
        # render a response
        self.render()