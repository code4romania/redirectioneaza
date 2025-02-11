import json
import random
from datetime import datetime
from typing import Dict, List, Union

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django.views.generic import TemplateView

from partners.models import Partner
from redirectioneaza.common.cache import cache_decorator

from ..models.donors import Donor
from ..models.ngos import FRONTPAGE_NGOS_KEY, FRONTPAGE_STATS_KEY, Ngo
from .base import BaseVisibleTemplateView
from .common import NgoSearchMixin


class HomePage(BaseVisibleTemplateView):
    template_name = "public/home.html"
    title = "redirectioneaza.ro"

    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=FRONTPAGE_STATS_KEY)
    def _get_stats(self, now: datetime = None, ngo_queryset: QuerySet = None) -> List[Dict[str, Union[str, int]]]:
        if now is None:
            now = timezone.now()

        if ngo_queryset is None:
            ngo_queryset = Ngo.active

        start_of_year = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)

        forms_filled_count = Donor.objects.filter(date_created__gte=start_of_year).count()
        pluralized_title = ngettext_lazy(
            "form filled in",
            "forms filled in",
            forms_filled_count,
        )

        return [
            {
                "title": _("organizations registered in the platform"),
                "value": ngo_queryset.count(),
            },
            {
                "title": pluralized_title + " " + str(start_of_year.year),
                "value": forms_filled_count,
            },
            {
                "title": _("redirected to NGOs through the platform"),
                "value": _("> €2 million"),
            },
        ]

    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=FRONTPAGE_NGOS_KEY)
    def _get_random_ngos(self, ngo_queryset: QuerySet, num_ngos: int):
        all_ngo_ids = list(Ngo.active.values_list("id", flat=True))
        return ngo_queryset.filter(id__in=random.sample(all_ngo_ids, num_ngos))

    def _partner_response(self, context: Dict, partner: Partner):
        partner_ngos = partner.ordered_ngos()
        context.update(
            {
                "company_name": partner.name,
                "has_custom_header": partner.has_custom_header,
                "has_custom_note": partner.has_custom_note,
                "ngos": partner_ngos,
            }
        )
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        now = timezone.now()

        context.update(
            {
                "title": "redirectioneaza.ro",
                "limit": settings.DONATIONS_LIMIT,
                "month_limit": settings.DONATIONS_LIMIT_MONTH_NAME,
                "current_year": now.year,
            }
        )

        partner: Partner = request.partner
        if partner:
            return self._partner_response(context, partner)

        ngo_queryset = Ngo.active

        context["stats"] = self._get_stats(now, ngo_queryset)
        context["ngos"] = self._get_random_ngos(ngo_queryset, num_ngos=min(4, ngo_queryset.count()))

        return context


class AboutHandler(BaseVisibleTemplateView):
    template_name = "public/articles/about.html"
    title = _("About redirectioneaza.ro")


class NgoListHandler(NgoSearchMixin):
    template_name = "public/all-ngos.html"
    context_object_name = "ngos"
    queryset = Ngo.active
    ordering = "name"
    paginate_by = 8

    def get_queryset(self):
        queryset = self.search()

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


class NoteHandler(BaseVisibleTemplateView):
    template_name = "public/articles/note.html"
    title = _("Information notice")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_email"] = settings.CONTACT_EMAIL_ADDRESS

        return context


class PolicyHandler(BaseVisibleTemplateView):
    template_name = "public/articles/policy.html"
    title = _("Privacy policy")


class TermsHandler(BaseVisibleTemplateView):
    template_name = "public/articles/terms.html"
    title = _("Terms & conditions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_email"] = settings.CONTACT_EMAIL_ADDRESS

        return context


class HealthCheckHandler(TemplateView):
    def get(self, request, *args, **kwargs):
        response = {
            "status": "OK",
            "version": settings.VERSION,
            "revision": settings.REVISION,
            "environment": settings.ENVIRONMENT,
        }

        return HttpResponse(
            content=json.dumps(response).encode("utf-8"),
            content_type="application/json",
        )


class EmailDemoHandler(BaseVisibleTemplateView):
    template_name = "emails"
    title = "Email demo"

    def get_context_data(self, **kwargs):
        email_path = kwargs.get("email_path_str")
        if not email_path:
            raise ValueError("Email path is required")
        email_path = email_path.replace("_", "/")
        self.template_name = f"{self.template_name}/{email_path}.html"

        context = super().get_context_data(**kwargs)

        context.update(
            {
                "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            }
        )

        query_params = self.request.GET.items()
        for key, value in query_params:
            context[key] = value

        return context
