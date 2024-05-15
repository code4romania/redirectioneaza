"""
URL configuration for the redirectioneaza project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https:/docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin, admin as django_admin
from django.urls import path, re_path
from django.views.generic import RedirectView

from donations.views.account_management import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    SetPasswordView,
    SignupView,
    VerificationView,
)
from donations.views.admin import (
    AdminHome,
    AdminNewNgoHandler,
    AdminNgoHandler,
    AdminNgosListByDate,
    AdminNgosListByForms,
    AdminNgosListByFormsNow,
    AdminNgosListByFormsPrevious,
    AdminNgosListByName,
    UserAccounts,
)
from donations.views.api import CheckNgoUrl, GetNgoForm, GetNgoForms, GetUploadUrl, NgosApi
from donations.views.cron import CustomExport, NgoExport, NgoRemoveForms, Stats
from donations.views.my_account import (
    ArchiveDownloadLinkView,
    MyAccountDetailsView,
    MyAccountView,
    NgoDetailsView,
)
from donations.views.ngo import DonationSucces, FormSignature, OwnFormDownloadLinkHandler, TwoPercentHandler
from donations.views.site import (
    AboutHandler,
    FAQHandler,
    ForNgoHandler,
    HealthCheckHandler,
    HomePage,
    NgoListHandler,
    NoteHandler,
    PolicyHandler,
    TermsHandler,
)

admin.site.site_header = f"Admin | {settings.VERSION_SUFFIX}"


urlpatterns = (
    [
        # the public part of the app
        path("", HomePage.as_view(), name="home"),
        path("ong/", ForNgoHandler.as_view(), name="ngo"),
        path("pentru-ong-uri/", RedirectView.as_view(pattern_name="ngo", permanent=True)),
        path("health/", HealthCheckHandler.as_view(), name="health-check"),
        path(
            "download/<donor_date_str>/<donor_id>/<donor_hash>/",
            OwnFormDownloadLinkHandler.as_view(),
            name="donor-download-link",
        ),
        # backup in case of old urls. to be removed
        path("organizatii/", NgoListHandler.as_view(), name="organizations"),
        path("asociatii/", RedirectView.as_view(pattern_name="organizations", permanent=True)),
        path("termene-si-conditii/", TermsHandler.as_view(), name="terms"),
        path("termeni/", RedirectView.as_view(pattern_name="terms", permanent=True)),
        path("TERMENI/", RedirectView.as_view(pattern_name="terms", permanent=True)),
        path("nota-de-informare/", NoteHandler.as_view(), name="note"),
        path("politica/", PolicyHandler.as_view(), name="policy"),
        path("despre/", AboutHandler.as_view(), name="about"),
        path("faq/", (FAQHandler.as_view()), name="faq"),
        # account management
        path("cont-nou/", SignupView.as_view(), name="signup"),
        path("login/", LoginView.as_view(), name="login"),
        path("logout/", LogoutView.as_view(), name="logout"),
        path("forgot/", ForgotPasswordView.as_view(), name="forgot"),
        # verification url: used for signup, and reset password
        path(
            "verify/<str:verification_type>/<uuid:user_id>-<uuid:signup_token>/",
            VerificationView.as_view(),
            name="verification",
        ),
        path("password/", SetPasswordView.as_view(), name="password"),
        # my account
        path("contul-meu/", MyAccountView.as_view(), name="contul-meu"),
        path("organizatia/", NgoDetailsView.as_view(), name="organization"),
        path("asociatia/", RedirectView.as_view(pattern_name="organization", permanent=True)),
        path("date-cont/", MyAccountDetailsView.as_view(), name="date-contul-meu"),
        # APIs
        path("api/ngo/check-url/<ngo_url>/", CheckNgoUrl.as_view(), name="api-ngo-check-url"),
        path("api/ngos/", NgosApi.as_view(), name="api-ngos"),
        #
        path("api/ngo/upload-url/", GetUploadUrl.as_view(), name="api-ngo-upload-url"),
        path("api/ngo/form/<ngo_url>/", GetNgoForm.as_view(), name="api-ngo-form-url"),
        path("api/ngo/forms/download/", GetNgoForms.as_view(), name="api-ngo-forms"),
        # Cron routes
        path("cron/stats/", Stats.as_view(), name="cron-stats"),
        path("cron/ngos/remove-form/", NgoRemoveForms.as_view(), name="cron-ngo-remove-form"),
        path("cron/ngos/export/", NgoExport.as_view(), name="cron-ngo-export"),
        path("cron/export/custom/", CustomExport.as_view(), name="cron-custom-export"),
        #
        path("admin/django/login/", RedirectView.as_view(pattern_name="login", permanent=True)),
        # Django Admin
        path("admin/django/", django_admin.site.urls),
        # ADMIN HANDLERS
        path("admin/ong-nou/", AdminNewNgoHandler.as_view(), name="admin-ong-nou"),
        path("admin/conturi/", UserAccounts.as_view(), name="admin-users"),
        path("admin/orgs/date/", AdminNgosListByDate.as_view(), name="admin-ngos-by-date"),
        path("admin/orgs/name/", AdminNgosListByName.as_view(), name="admin-ngos-by-name"),
        path("admin/orgs/forms/", AdminNgosListByForms.as_view(), name="admin-ngos-by-forms"),
        path("admin/orgs/forms-current/", AdminNgosListByFormsNow.as_view(), name="admin-ngos-by-forms-now"),
        path("admin/orgs/forms-previous/", AdminNgosListByFormsPrevious.as_view(), name="admin-ngos-by-forms-prev"),
        path(
            "admin/organizatii/",
            RedirectView.as_view(pattern_name="admin-ngos-by-date", permanent=True),
            name="admin-ngos",
        ),
        path("admin/<ngo_url>/", AdminNgoHandler.as_view(), name="admin-ong"),
        path("admin/download/<job_id>/", ArchiveDownloadLinkView.as_view(), name="admin-download-link"),
        path("admin/", AdminHome.as_view(), name="admin-index"),  # name was "admin"
        # must always be the last set of urls
        re_path(r"^(?P<ngo_url>[\w-]+)/doilasuta/", RedirectView.as_view(pattern_name="twopercent", permanent=True)),
        re_path(r"^(?P<ngo_url>[\w-]+)/semnatura/", FormSignature.as_view(), name="ngo-twopercent-signature"),
        re_path(r"^(?P<ngo_url>[\w-]+)/succes/", DonationSucces.as_view(), name="ngo-twopercent-success"),
        re_path(r"^(?P<ngo_url>[\w-]+)/$", TwoPercentHandler.as_view(), name="twopercent"),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
