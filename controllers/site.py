# -*- coding: utf-8 -*-


from models.handlers import BaseHandler



"""
Handlers used for site routing
"""
class HomePage(BaseHandler):
    template_name = 'index.html'
    def get(self):

        self.template_values["title"] = "donez si eu"
                
        # render a response
        self.render()

class AboutHandler(BaseHandler):
    template_name = 'teacher.html'
    def get(self):
        self.abort(404)
        self.template_values["title"] = "Teacher"

        # render a response
        self.render()


class TermsHandler(BaseHandler):
    template_name = 'terms.html'
    def get(self):

        self.template_values["title"] = "Termeni si conditii"

        # render a response
        self.render()



class PolicyHandler(BaseHandler):
    template_name = 'policy.html'
    def get(self):

        self.template_values["title"] = "Politica de confidentialitate"

        # render a response
        self.render()
