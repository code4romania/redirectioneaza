from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from donations.views.ngo_account.byof import NgoBringYourOwnFormLinkView, NgoBringYourOwnFormView
from donations.views.ngo_account.causes import NgoCauseCreateView, NgoCauseEditView, NgoCausesListView
from donations.views.ngo_account.my_organization import NgoMainCauseView, NgoPresentationView
from donations.views.ngo_account.redirections import (
    ArchiveDownloadLinkView,
    NgoArchivesView,
    NgoRedirectionsView,
    RedirectionDownloadLinkView,
    RedirectionsDownloadJobLinkView,
    RedirectionsDownloadsView,
)
from donations.views.ngo_account.user_settings import UserSettingsView

admin.site.site_header = f"Admin | {settings.VERSION_LABEL}"


urlpatterns = [
    # XXX: This is for when we'll have a dashboard
    # path("/", NgoDashboardView.as_view(), name="dashboard"),
    path("prezentare/", NgoPresentationView.as_view(), name="presentation"),
    path("", RedirectView.as_view(pattern_name="my-organization:presentation"), name="dashboard"),
    path("formular/", NgoMainCauseView.as_view(), name="form"),
    path("formulare/", RedirectView.as_view(pattern_name="my-organization:form"), name="forms-redirect"),
    path("redirectionari/", NgoRedirectionsView.as_view(), name="redirections"),
    path("redirectionari/arhive/", NgoArchivesView.as_view(), name="archives"),
    path(
        "arhive/",
        RedirectView.as_view(pattern_name="my-organization:archives", permanent=True),
        name="archives-redirect",
    ),
    path("redirectionari/arhive/<job_id>/", ArchiveDownloadLinkView.as_view(), name="archive-download-link"),
    path(
        "arhiva/<job_id>/",
        RedirectView.as_view(pattern_name="my-organization:archive-download-link", permanent=True),
        name="archive-download-link-redirect",
    ),
    path("setari-cont/", UserSettingsView.as_view(), name="settings-account"),
    path("formular/<form_id>/", RedirectionDownloadLinkView.as_view(), name="redirection-download-link"),
]

if settings.ENABLE_MULTIPLE_FORMS:
    urlpatterns += [
        path("cauze/", NgoCausesListView.as_view(), name="causes"),
        path("cauze/creeaza", NgoCauseCreateView.as_view(), name="cause-create"),
        path("cauze/<cause_id>/", NgoCauseEditView.as_view(), name="cause"),
    ]

if settings.ENABLE_BYOF:
    urlpatterns += [
        path("redirectionari/extern/", NgoBringYourOwnFormView.as_view(), name="byof"),
        path("redirectionari/extern/<job_id>/", NgoBringYourOwnFormLinkView.as_view(), name="byof-download-link"),
    ]

if settings.ENABLE_CSV_DOWNLOAD:
    urlpatterns += [
        path("redirectionari/descarcari/", RedirectionsDownloadsView.as_view(), name="downloads"),
        path(
            "redirectionari/descarcari/<job_id>/",
            RedirectionsDownloadJobLinkView.as_view(),
            name="redirections-download-link",
        ),
    ]
