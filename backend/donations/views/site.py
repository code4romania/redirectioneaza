from datetime import datetime

from django.shortcuts import redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .base import BaseHandler
from ..models.main import Ngo, Donor


class HomePage(BaseHandler):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        now = timezone.now()

        # TODO: the search isn't working
        context = {
            "title": "redirectioneaza.ro",
            "limit": settings.DONATIONS_LIMIT,
            "DEFAULT_NGO_LOGO": settings.DEFAULT_NGO_LOGO,
            "current_year": now.year,
        }

        if request.partner:
            context.update(
                {
                    "company_name": request.partner.name,
                    "custom_header": request.partner.has_custom_header,
                    "custom_note": request.partner.has_custom_note,
                    "ngos": request.partner.ngos.filter(is_active=True).order_by("name"),
                }
            )
        else:
            context["stats"] = {
                "ngos": Ngo.objects.count(),
                "forms": Donor.objects.filter(date_created__gte=datetime(now.year, 1, 1)).count(),
            }
            context["ngos"] = Ngo.objects.filter(is_active=True).order_by("name")

        return render(request, self.template_name, context)


class AboutHandler(BaseHandler):
    template_name = "despre.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Despre Redirectioneaza.ro"}
        return render(request, self.template_name, context)


class ForNgoHandler(BaseHandler):
    template_name = "for-ngos.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("contul-meu"))

        context = {"title": "Pentru ONG-uri"}
        return render(request, self.template_name, context)


class NgoListHandler(BaseHandler):
    template_name = "all-ngos.html"

    def get(self, request, *args, **kwargs):
        # TODO: the search isn't working
        # TODO: add pagination
        context = {
            "title": "Toate ONG-urile",
            "ngos": Ngo.objects.filter(is_active=True).order_by("name"),
        }

        return render(request, self.template_name, context)


class NoteHandler(BaseHandler):
    template_name = "note.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Notă de informare"}
        return render(request, self.template_name, context)


class PolicyHandler(BaseHandler):
    template_name = "policy.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Politica de confidențialitate"}
        return render(request, self.template_name, context)


class TermsHandler(BaseHandler):
    template_name = "terms.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Termeni și condiții"}
        return render(request, self.template_name, context)
