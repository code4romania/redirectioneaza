# -*- coding: utf-8 -*-


from models.handlers import BaseHandler



"""
Handlers used for site routing
"""
class HomePage(BaseHandler):
    def get(self):

        # set the index template
        self.set_template('index.html')

        header = {}
        header["title"] = u"Învață după cele mai bune cursuri"
        header["description"] = "Cursuri gratuite"
        
        
        # render a response
        self.render()

class AboutHandler(BaseHandler):
    def get(self):

        # set the index template
        self.set_template('teacher.html')
        self.template_values["title"] = "Teacher"

        # render a response
        self.render()

class NewAccountHandler(BaseHandler):
    def get(self):

        # set the index template
        self.set_template('student.html')
        self.template_values["title"] = "Student"

        header = {}
        header["title"] = "Titlul paginii"
        header["image"] = ""

        self.template_values["header"] = header

        # render a response
        self.render()
