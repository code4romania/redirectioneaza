from django.conf import settings
from django.contrib import admin
from django.urls import path

from donations.views.ngo_account import (
    NgoDetailsView,
    NgoFormsView,
    NgoRedirectionsView,
)

admin.site.site_header = f"Admin | {settings.VERSION_LABEL}"


urlpatterns = [
    path("prezentare/", NgoDetailsView.as_view(), name="organization-presentation"),
    path("formulare/", NgoFormsView.as_view(), name="organization-forms"),
    path("redirectionari/", NgoRedirectionsView.as_view(), name="organization-redirections"),
]
