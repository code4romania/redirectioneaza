from django.shortcuts import render
from django.conf import settings

from .base import BaseHandler


class HomePage(BaseHandler):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        context = {
            "title": "redirectioneaza.ro",
            "limit": settings.DONATIONS_LIMIT,
            "DEFAULT_NGO_LOGO": settings.DEFAULT_NGO_LOGO,
            "ngos": [],
        }

        return render(request, self.template_name, context)


class AboutHandler(BaseHandler):
    template_name = "despre.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["title"] = "Despre Redirectioneaza.ro"
        return render(request, self.template_name, context)


class ForNgoHandler(BaseHandler):
    template_name = "for-ngos.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["title"] = "Pentru ONG-uri"
        return render(request, self.template_name, context)


class NgoListHandler(BaseHandler):
    pass


class NoteHandler(BaseHandler):
    template_name = "note.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["title"] = "Notă de informare"
        return render(request, self.template_name, context)


class PolicyHandler(BaseHandler):
    template_name = "policy.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["title"] = "Politica de confidențialitate"
        return render(request, self.template_name, context)


class TermsHandler(BaseHandler):
    template_name = "terms.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["title"] = "Termeni și condiții"
        return render(request, self.template_name, context)
