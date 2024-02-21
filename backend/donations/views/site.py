import random
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from redirectioneaza.common.cache import cache_decorator
from .base import BaseHandler
from ..models.main import Ngo, Donor


class HomePage(BaseHandler):
    template_name = "index.html"

    @staticmethod
    @cache_decorator(cache_key_prefix="ALL_NGO_IDS", timeout=settings.CACHE_TIMEOUT_MEDIUM)
    def _get_list_of_ngo_ids() -> list:
        return list(Ngo.active.values_list("id", flat=True))

    def get(self, request, *args, **kwargs):
        now = timezone.now()

        context = {
            "title": "redirectioneaza.ro",
            "limit": settings.DONATIONS_LIMIT,
            "DEFAULT_NGO_LOGO": settings.DEFAULT_NGO_LOGO,
            "current_year": now.year,
        }

        if request.partner:
            ngo_queryset = request.partner.ngos
            context.update(
                {
                    "company_name": request.partner.name,
                    "custom_header": request.partner.has_custom_header,
                    "custom_note": request.partner.has_custom_note,
                }
            )
        else:
            ngo_queryset = Ngo.active
            start_of_year = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
            context["stats"] = {
                "ngos": ngo_queryset.count(),
                "forms": Donor.objects.filter(date_created__gte=start_of_year).count(),
            }

        all_ngo_ids = self._get_list_of_ngo_ids()
        context["ngos"] = ngo_queryset.filter(id__in=random.sample(all_ngo_ids, 4))

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
            "ngos": Ngo.active.order_by("name"),
            "DEFAULT_NGO_LOGO": settings.DEFAULT_NGO_LOGO,
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


class HealthCheckHandler(BaseHandler):
    def get(self, request, *args, **kwargs):
        # return HttpResponse(str(request.headers))
        return HttpResponse("OK")
