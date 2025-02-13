from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from donations.views.ngo_account import (
    ArchiveDownloadLinkView,
    NgoArchivesView,
    NgoFormsView,
    NgoPresentationView,
    NgoRedirectionsView,
    UserSettingsView,
)

admin.site.site_header = f"Admin | {settings.VERSION_LABEL}"


urlpatterns = [
    # XXX: This is for when we'll have a dashboard
    # path("/", NgoDashboardView.as_view(), name="dashboard"),
    path("prezentare/", NgoPresentationView.as_view(), name="presentation"),
    path("", RedirectView.as_view(pattern_name="my-organization:presentation"), name="dashboard"),
    path("formulare/", NgoFormsView.as_view(), name="forms"),
    path("redirectionari/", NgoRedirectionsView.as_view(), name="redirections"),
    path("arhive/", NgoArchivesView.as_view(), name="archives"),
    path("setari-cont/", UserSettingsView.as_view(), name="settings-account"),
    path("arhiva/<job_id>/", ArchiveDownloadLinkView.as_view(), name="archive-download-link"),
]
