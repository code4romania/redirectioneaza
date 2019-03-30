# -*- coding: utf-8 -*-
from flask import render_template

from redirectioneaza.config import DEFAULT_NGO_LOGO
from redirectioneaza.handlers.base import BaseHandler
from redirectioneaza.models import NgoEntity

"""
Handlers used for site routing
"""


class HomePage(BaseHandler):
    template_name = 'index.html'

    def get(self):

        self.template_values["title"] = "redirectioneaza 2%"

        _ngos = NgoEntity.query.limit(4).all()

        self.template_values["ngos"] = _ngos
        self.template_values["DEFAULT_NGO_LOGO"] = DEFAULT_NGO_LOGO

        # render a response
        return render_template(self.template_name, **self.template_values)


class ForNgoHandler(BaseHandler):
    template_name = 'for-ngos.html'

    def get(self):
        # self.abort(404)
        self.template_values["title"] = "Pentru ONG-uri"

        # render a response
        return render_template(self.template_name, **self.template_values)


class NgoListHandler(BaseHandler):
    template_name = 'all-ngos.html'

    def get(self):
        # self.abort(404)
        self.template_values["title"] = "Asociatii"

        ngos = NgoEntity.query.filter_by(active=True).all()
        self.template_values["ngos"] = ngos
        self.template_values["DEFAULT_NGO_LOGO"] = DEFAULT_NGO_LOGO

        # render a response
        return render_template(self.template_name, **self.template_values)


class TermsHandler(BaseHandler):
    template_name = 'terms.html'

    def get(self):
        self.template_values["title"] = "Termeni si conditii"

        # render a response
        return render_template(self.template_name, **self.template_values)


class NoteHandler(BaseHandler):
    template_name = 'note.html'

    def get(self):
        self.template_values["title"] = "Nota de informare"

        # render a response
        return render_template(self.template_name, **self.template_values)


class AboutHandler(BaseHandler):
    template_name = 'despre.html'

    def get(self):
        self.template_values["title"] = "Despre Redirectioneaza.ro"

        # render a response
        return render_template(self.template_name, **self.template_values)


class PolicyHandler(BaseHandler):
    template_name = 'policy.html'

    def get(self):
        self.template_values["title"] = "Politica de confidentialitate"

        # render a response
        return render_template(self.template_name, **self.template_values)