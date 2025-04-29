from typing import Any, Callable, Dict, List, Optional, Union

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, OuterRef, QuerySet, Subquery
from django.db.models.functions import JSONObject
from django.http import Http404, HttpRequest, QueryDict
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from donations.models import RedirectionsDownloadJob
from donations.models.donors import Donor
from donations.models.jobs import Job
from donations.models.ngos import Cause, NGO_CAUSES_QUERY_CACHE_KEY, Ngo
from donations.views.base import BaseVisibleTemplateView
from donations.views.common.misc import get_ngo_archive_download_status, get_time_between_retries
from donations.views.common.search import DonorSearchMixin
from donations.views.ngo_account.common import FileDownloadProxy, NgoBaseListView
from donations.views.ngo_account_filters import (
    get_active_filters_values,
    get_queryset_filters,
    get_redirections_filters,
)
from redirectioneaza.common.cache import cache_decorator
from redirectioneaza.common.filters import QueryFilter
from users.models import User


class NgoRedirectionsView(NgoBaseListView, DonorSearchMixin):
    template_name = "ngo-account/redirections/main.html"
    title = _("Redirections")
    context_object_name = "redirections"
    paginate_by = 8
    tab_title = "redirections"
    sidebar_item_target = "org-redirections"

    def get_context_data(self, **kwargs):
        search_query = self._search_query()

        query_dict = QueryDict(mutable=True)
        query_dict["q"] = search_query
        query_dict["year"] = self.request.GET.get("year", "")
        query_dict["county"] = self.request.GET.get("county", "")
        query_dict["city"] = self.request.GET.get("city", "")
        query_dict["period"] = self.request.GET.get("period", "")
        query_dict["signed"] = self.request.GET.get("signed", "")
        query_dict["anonymous"] = self.request.GET.get("anonymous", "")

        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        causes = self._get_ngo_causes(ngo=ngo) if ngo else None
        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "active_tab": self.tab_title,
                "causes": causes,
                "period_between_retries": get_time_between_retries(),
                "search_query": search_query,
                "url_search_query": query_dict.urlencode(),
                "filters": self.get_filters_dict(ngo=ngo),
                "filters_active": self.get_frontend_filters(
                    filters=self.get_filters(ngo=ngo),
                    request_params=self.request.GET,
                ),
                "limit_rows": settings.DONATIONS_CSV_LIMIT_PER_FILE,
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
        return get_redirections_filters(ngo=ngo)

    def get_filters_dict(self, ngo: Ngo) -> List[Dict[str, Union[str, Callable, Optional[List[Dict]]]]]:
        objects = self.object_list
        return [
            query_filter.to_dict(include_options=True, objects=objects) for query_filter in (self.get_filters(ngo=ngo))
        ]

    def get_frontend_filters(self, filters: List[QueryFilter], request_params: Dict) -> Dict[str, Any]:
        return get_active_filters_values(filters=filters, request_params=request_params)

    def get_queryset_filters(self, filters: List[QueryFilter], request_params: QueryDict) -> Dict[str, Any]:
        return get_queryset_filters(filters=filters, request_params=request_params)

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        if not ngo:
            return Donor.objects.none()

        queryset_filters = self.get_queryset_filters(filters=self.get_filters(ngo=ngo), request_params=self.request.GET)

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


class NgoArchivesView(NgoBaseListView):
    template_name = "ngo-account/archives/main.html"
    title = _("Archives history")
    context_object_name = "archive_jobs"
    paginate_by = 8
    tab_title = "archives"
    sidebar_item_target = "org-archives"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "active_tab": self.tab_title,
            }
        )

        return context

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        archives = Job.objects.none()
        if ngo:
            archives = (
                ngo.jobs.prefetch_related("cause")
                .all()
                .order_by("-date_created")
                .values(
                    "pk",
                    "date_created",
                    "number_of_donations",
                    "status",
                    "cause__name",
                )
            )

        return archives


class RedirectionsDownloadsView(NgoBaseListView):
    template_name = "ngo-account/redirections-downloads/main.html"
    title = _("Redirections downloads")
    context_object_name = "download_jobs"
    paginate_by = 8
    tab_title = "downloads"
    sidebar_item_target = "org-downloads"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "active_tab": self.tab_title,
            }
        )

        return context

    def get_queryset(self):
        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        downloads = RedirectionsDownloadJob.objects.none()
        if ngo:
            downloads = (
                ngo.download_jobs.all()
                .order_by("-date_created")
                .values(
                    "pk",
                    "date_created",
                    "output_rows",
                    "queryset",
                    "status",
                )
            )

        return downloads


class ArchiveDownloadLinkView(BaseVisibleTemplateView):
    title = _("Download archive")

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request: HttpRequest, job_id, *args, **kwargs):
        user: User = request.user

        if user.has_perm("users.can_view_old_dashboard"):
            # The admin can always get the download link
            try:
                job = Job.objects.get(pk=job_id)
            except Job.DoesNotExist:
                raise Http404

        elif not user.ngo:
            # Users without NGOs don't have any download links anyway
            raise Http404

        else:
            # Check that the current user's NGO is active
            if not user.ngo.is_active:
                raise Http404

            # Check that the requested job belongs to the current user
            try:
                job = Job.objects.get(pk=job_id, ngo=user.ngo)
            except Job.DoesNotExist:
                raise Http404

        # Check that the job has a zip file
        if not job.zip:
            raise Http404

        return redirect(job.zip.url)


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


class RedirectionsDownloadJobLinkView(FileDownloadProxy):
    model = RedirectionsDownloadJob

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request: HttpRequest, job_id, *args, **kwargs):
        user: User = request.user

        if not self.is_user_valid(user):
            raise Http404

        download: RedirectionsDownloadJob = self.get_downloadable_object(user=user, pk=job_id)

        # Check that the job has a zip file
        if not download.output_file:
            raise Http404

        return redirect(download.output_file.url)
