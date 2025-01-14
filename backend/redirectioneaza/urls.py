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
from django.contrib import admin
from django.urls import include, path, re_path, reverse
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
from donations.views.api import (
    CheckNgoUrl,
    GetNgoForm,
    GetNgoForms,
    GetUploadUrl,
    NgosApi,
    SearchNgosApi,
    UpdateFromNgohub,
)
from donations.views.cron import CustomExport, NgoExport, NgoRemoveForms
from donations.views.ngo_account import (
    ArchiveDownloadLinkView,
    MyAccountDetailsView,
    MyAccountView,
    NewNgoDetailsView,
)
from donations.views.redirections import DonationSucces, FormSignature, OwnFormDownloadLinkHandler, TwoPercentHandler
from donations.views.site import (
    AboutHandler,
    HealthCheckHandler,
    HomePage,
    NgoListHandler,
    NoteHandler,
    PolicyHandler,
    TermsHandler,
)
from frequent_questions.views import FAQHandler
from redirectioneaza.views import StaticPageView

admin.site.site_header = f"Admin | {settings.VERSION_LABEL}"


urlpatterns = (
    [
        # the public part of the app
        path("", HomePage.as_view(), name="home"),
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
        path("ong/", RedirectView.as_view(pattern_name="signup", permanent=True)),
        path("pentru-ong-uri/", RedirectView.as_view(pattern_name="signup", permanent=True)),
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
        path("organizatia/", NewNgoDetailsView.as_view(), name="organization"),
        path("asociatia/", RedirectView.as_view(pattern_name="organization", permanent=True)),
        path("date-cont/", MyAccountDetailsView.as_view(), name="date-contul-meu"),
        path(
            "contul-meu/eroare/aplicatie-lipsa/",
            StaticPageView.as_view(template_name="account/errors/login/app_missing.html"),
            name="error-app-missing",
        ),
        path(
            "contul-meu/eroare/sincronizare-ong/",
            StaticPageView.as_view(template_name="account/errors/login/multiple_ngos.html"),
            name="error-multiple-organizations",
        ),
        path(
            "contul-meu/eroare/rol-necunoscut/",
            StaticPageView.as_view(template_name="account/errors/login/unknown_role.html"),
            name="error-unknown-user-role",
        ),
        # APIs
        path("api/ngohub-refresh/", UpdateFromNgohub.as_view(), name="api-ngohub-refresh"),
        path("api/ngo/check-url/<ngo_url>/", CheckNgoUrl.as_view(), name="api-ngo-check-url"),
        path("api/ngos/", NgosApi.as_view(), name="api-ngos"),
        #
        path("api/ngo/upload-url/", GetUploadUrl.as_view(), name="api-ngo-upload-url"),
        path("api/ngo/form/<ngo_url>/", GetNgoForm.as_view(), name="api-ngo-form-url"),
        path("api/ngo/forms/download/", GetNgoForms.as_view(), name="api-ngo-forms"),
        #
        path("api/search/", SearchNgosApi.as_view(), name="api-search-ngos"),
        # Cron routes
        path("cron/ngos/remove-form/", NgoRemoveForms.as_view(), name="cron-ngo-remove-form"),
        path("cron/ngos/export/", NgoExport.as_view(), name="cron-ngo-export"),
        path("cron/export/custom/", CustomExport.as_view(), name="cron-custom-export"),
        # Django Admin
        path("admin/django/", RedirectView.as_view(pattern_name="admin:index", permanent=True)),
        path("admin/avansat/login/", RedirectView.as_view(pattern_name="login", permanent=True)),
        path("admin/avansat/", admin.site.urls),
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
        # Skip the login provider selector page and redirect to Cognito
        path(
            "allauth/login/",
            RedirectView.as_view(
                url=f'/allauth{reverse("amazon_cognito_login", urlconf="allauth.urls")}',
                permanent=True,
            ),
        ),
        path("allauth/", include("allauth.urls")),
        path("tinymce/", include("tinymce.urls")),
        path("robots.txt", StaticPageView.as_view(template_name="robots.txt", content_type="text/plain")),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
