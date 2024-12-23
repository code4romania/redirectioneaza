import random
from datetime import datetime
from typing import Dict, List, Union

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from partners.models import DisplayOrderingChoices
from redirectioneaza.common.cache import cache_decorator

from ..models.donors import Donor
from ..models.ngos import ALL_NGO_IDS_CACHE_KEY, FRONTPAGE_NGOS_KEY, FRONTPAGE_STATS_KEY, Ngo
from .common import SearchMixin


class HomePage(TemplateView):
    template_name = "public/home.html"

    @staticmethod
    @cache_decorator(timeout=settings.TIMEOUT_CACHE_LONG, cache_key_prefix=ALL_NGO_IDS_CACHE_KEY)
    def _get_list_of_ngo_ids() -> list:
        return list(Ngo.active.values_list("id", flat=True))

    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=FRONTPAGE_STATS_KEY)
    def _get_stats(self, now: datetime = None, ngo_queryset: QuerySet = None) -> List[Dict[str, Union[str, int]]]:
        if now is None:
            now = timezone.now()

        if ngo_queryset is None:
            ngo_queryset = Ngo.active

        start_of_year = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
        return [
            {
                "title": _("organizations registered in the platform"),
                "value": ngo_queryset.count(),
            },
            {
                "title": _("forms filled in") + " " + str(start_of_year.year),
                "value": Donor.objects.filter(date_created__gte=start_of_year).count(),
            },
            {
                "title": _("redirected to NGOs through the platform"),
                "value": _("> €2 million"),
            },
        ]

    def get(self, request, *args, **kwargs):
        now = timezone.now()

        context = {
            "title": "redirectioneaza.ro",
            "limit": settings.DONATIONS_LIMIT,
            "month_limit": settings.DONATIONS_LIMIT_MONTH_NAME,
            "current_year": now.year,
        }

        if partner := request.partner:
            partner_ngos = partner.ngos.all()

            if partner.display_ordering == DisplayOrderingChoices.ALPHABETICAL:
                partner_ngos = partner_ngos.order_by("name")
            elif partner.display_ordering == DisplayOrderingChoices.NEWEST:
                partner_ngos = partner_ngos.order_by("-date_created")
            elif partner.display_ordering == DisplayOrderingChoices.RANDOM:
                random.shuffle(list(partner_ngos))

            context.update(
                {
                    "company_name": partner.name,
                    "custom_header": partner.has_custom_header,
                    "custom_note": partner.has_custom_note,
                    "ngos": partner_ngos,
                }
            )
        else:
            ngo_queryset = Ngo.active

            context["stats"] = self._get_stats(now, ngo_queryset)
            context["ngos"] = self._get_random_ngos(ngo_queryset, num_ngos=min(4, ngo_queryset.count()))

        return render(request, self.template_name, context)

    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=FRONTPAGE_NGOS_KEY)
    def _get_random_ngos(self, ngo_queryset: QuerySet, num_ngos: int):
        all_ngo_ids = self._get_list_of_ngo_ids()
        return ngo_queryset.filter(id__in=random.sample(all_ngo_ids, num_ngos))


class AboutHandler(TemplateView):
    template_name = "public/about.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Despre redirectioneaza.ro"}
        return render(request, self.template_name, context)


class NgoListHandler(SearchMixin):
    template_name = "public/all-ngos.html"
    context_object_name = "ngos"
    queryset = Ngo.active
    ordering = "name"
    paginate_by = 8

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = self.search(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Toate ONG-urile",
                "limit": settings.DONATIONS_LIMIT,
                "month_limit": settings.DONATIONS_LIMIT_MONTH_NAME,
            }
        )
        return context


class NoteHandler(TemplateView):
    template_name = "public/note.html"

    def get(self, request, *args, **kwargs):
        context = {
            "title": "Notă de informare",
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        return render(request, self.template_name, context)


class PolicyHandler(TemplateView):
    template_name = "public/policy.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Politica de confidențialitate"}
        return render(request, self.template_name, context)


class TermsHandler(TemplateView):
    template_name = "public/terms.html"

    def get(self, request, *args, **kwargs):
        context = {
            "title": "Termeni și condiții",
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        return render(request, self.template_name, context)


class HealthCheckHandler(TemplateView):
    def get(self, request, *args, **kwargs):
        # return HttpResponse(str(request.headers))
        return HttpResponse("OK")
