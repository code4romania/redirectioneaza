from typing import Callable, Dict, List, Optional, Union

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, OuterRef, QuerySet, Subquery
from django.db.models.functions import JSONObject
from django.http import Http404, QueryDict
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from donations.models.donors import Donor
from donations.models.jobs import Job
from donations.models.ngos import Cause, NGO_CAUSES_QUERY_CACHE_KEY, Ngo
from donations.views.base import BaseVisibleTemplateView
from donations.views.common.misc import get_ngo_archive_download_status, get_time_between_retries
from donations.views.common.search import DonorSearchMixin
from donations.views.ngo_account.common import NgoBaseListView
from donations.views.ngo_account_filters import (
    CauseQueryFilter,
    CountyQueryFilter,
    FormPeriodQueryFilter,
    FormStatusQueryFilter,
    LocalityQueryFilter,
)
from redirectioneaza.common.cache import cache_decorator
from redirectioneaza.common.filters import QueryFilter
from users.models import User


class NgoRedirectionsView(NgoBaseListView, DonorSearchMixin):
    template_name = "ngo-account/redirections/main.html"
    title = _("Redirections")
    context_object_name = "redirections"
    paginate_by = 8
    sidebar_item_target = "org-redirections"

    def get_context_data(self, **kwargs):
        search_query = self._search_query()

        query_dict = QueryDict(mutable=True)
        query_dict["q"] = search_query

        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        causes = self._get_ngo_causes(ngo=ngo) if ngo else None
        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "causes": causes,
                "period_between_retries": get_time_between_retries(),
                "search_query": search_query,
                "url_search_query": query_dict.urlencode(),
                "filters": self.get_filters_dict(ngo=ngo),
                "filters_active": self.get_frontend_filters(ngo=ngo),
            }
        )

        if search_placeholder := self._search_placeholder():
            context["search_placeholder"] = search_placeholder

        context.update(get_ngo_archive_download_status(ngo))

        return context

    @cache_decorator(
        timeout=min(settings.TIMEOUT_CACHE_NORMAL, settings.TIMEDELTA_FORMS_DOWNLOAD_MINUTES),
        cache_key_custom=NGO_CAUSES_QUERY_CACHE_KEY,
    )
    def _get_ngo_causes(self, *, ngo: Ngo) -> QuerySet:
        if not ngo:
            return Cause.objects.none()

        if ngo.causes.count() == 0:
            return Cause.objects.none()

        ngo_archive_jobs: QuerySet[Job, Dict[str, str]] = (
            Job.objects.filter(ngo=ngo, cause=OuterRef("pk"))
            .order_by("-date_created")
            .values(obj=JSONObject(date_created=F("date_created"), status=F("status")))
        )

        return (
            ngo.causes.annotate(
                redirections_count=Count("donor"),
                last_archive_job=Subquery(ngo_archive_jobs[:1]),
            )
            .values(
                "name",
                "slug",
                "is_main",
                "redirections_count",
                "last_archive_job",
            )
            .filter(allow_online_collection=True)
            .order_by("-redirections_count", "name")
        )

    def get_filters(self, ngo: Ngo) -> List[QueryFilter]:
        return [
            CountyQueryFilter(ngo=ngo),
            LocalityQueryFilter(ngo=ngo),
            FormPeriodQueryFilter(ngo=ngo),
            FormStatusQueryFilter(ngo=ngo),
            CauseQueryFilter(ngo=ngo),
        ]

    def get_filters_dict(self, ngo: Ngo) -> List[Dict[str, Union[str, Callable, Optional[List[Dict]]]]]:
        objects = self.object_list
        return [
            query_filter.to_dict(include_options=True, objects=objects) for query_filter in (self.get_filters(ngo=ngo))
        ]

    def get_frontend_filters(self, ngo: Ngo, filters: List[QueryFilter] = None):
        if not filters:
            filters = self.get_filters(ngo=ngo)

        filters_active = {}
        request_params = self.request.GET

        for search_filter in filters:
            filter_key = search_filter.key
            if filter_value := request_params.get(filter_key, ""):
                filters_active[filter_key] = filter_value

        return filters_active

    def get_queryset_filters(self, ngo: Ngo, filters: List[QueryFilter] = None):
        if not filters:
            filters = self.get_filters(ngo=ngo)

        queryset_filters = {}
        request_params = self.request.GET

        for search_filter in filters:
            filter_key = search_filter.key
            if filter_value := request_params.get(filter_key, ""):
                queryset_filters[search_filter.queryset_key] = search_filter.transform(filter_value)

        return queryset_filters

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        if not ngo:
            return Donor.objects.none()

        queryset_filters = self.get_queryset_filters(ngo=ngo)

        redirections = (
            ngo.donor_set.all()
            .order_by("-date_created")
            .filter(is_available=True)
            .filter(**queryset_filters)
            .values(
                "id",
                "f_name",
                "l_name",
                "city",
                "county",
                "email",
                "phone",
                "date_created",
                "two_years",
                "is_anonymous",
                "has_signed",
            )
        )

        return self.search(queryset=redirections)


class RedirectionDownloadLinkView(BaseVisibleTemplateView):
    title = _("Download donor form")

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, form_id, *args, **kwargs):
        user: User = request.user
        ngo: Ngo = user.ngo if user.ngo else None

        if not ngo:
            raise Http404

        if not ngo.is_active:
            raise PermissionDenied(_("Your organization is not active"))

        try:
            donor = Donor.objects.get(pk=form_id, ngo=ngo)
        except Donor.DoesNotExist:
            raise Http404

        if not donor.pdf_file:
            raise Http404

        return redirect(donor.pdf_file.url)
