from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from donations.views.ngo_account import (
    NgoArchivesView,
    NgoDetailsView,
    NgoFormsView,
    NgoRedirectionsView,
    NgoSettingsView,
)

admin.site.site_header = f"Admin | {settings.VERSION_LABEL}"


urlpatterns = [
    # XXX: This is for when we'll have a dashboard
    # path("/", NgoDashboardView.as_view(), name="dashboard"),
    path("prezentare/", NgoDetailsView.as_view(), name="presentation"),
    path("", RedirectView.as_view(pattern_name="my-organization:presentation"), name="dashboard"),
    path("formulare/", NgoFormsView.as_view(), name="forms"),
    path("redirectionari/", NgoRedirectionsView.as_view(), name="redirections"),
    path("arhive/", NgoArchivesView.as_view(), name="archives"),
    path("settings/", NgoSettingsView.as_view(), name="settings"),
]
