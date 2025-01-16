from django.conf import settings
from django.contrib import admin
from django.urls import path

from donations.views.ngo_account import (
    NgoArchivesView,
    NgoDetailsView,
    NgoFormsView,
    NgoRedirectionsView,
)

admin.site.site_header = f"Admin | {settings.VERSION_LABEL}"


urlpatterns = [
    path("prezentare/", NgoDetailsView.as_view(), name="presentation"),
    path("formulare/", NgoFormsView.as_view(), name="forms"),
    path("redirectionari/", NgoRedirectionsView.as_view(), name="redirections"),
    path("arhive/", NgoArchivesView.as_view(), name="archives"),
]
