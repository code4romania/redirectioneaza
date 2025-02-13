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
    SignupConfirmationView,
    SignupVerificationView,
    SignupView,
    VerificationView,
)
from donations.views.api import (
    DownloadNgoForms,
    GetNgoForm,
    GetUploadUrl,
    SearchNgosApi,
    UpdateFromNgohub,
)
from donations.views.cron import NgoRemoveForms
from donations.views.errors import create_error_view
from donations.views.redirections import (
    OwnFormDownloadLinkHandler,
    RedirectionHandler,
    RedirectionSuccessHandler,
)
from donations.views.site import (
    AboutHandler,
    EmailDemoHandler,
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
        path("confirmare-cont/", SignupConfirmationView.as_view(), name="signup-confirmation"),
        path("validare-cont/", SignupVerificationView.as_view(), name="signup-verification"),
        path("ong/", RedirectView.as_view(pattern_name="signup", permanent=True)),
        path("pentru-ong-uri/", RedirectView.as_view(pattern_name="signup", permanent=True)),
        path("login/", LoginView.as_view(), name="login"),
        path("logout/", LogoutView.as_view(), name="logout"),
        path("recuperare-parola/", ForgotPasswordView.as_view(), name="forgot"),
        path("forgot/", RedirectView.as_view(pattern_name="forgot", permanent=True)),
        # verification url: used for signup, and reset password
        path(
            "verify/<str:verification_type>/<uuid:user_id>-<uuid:signup_token>/",
            VerificationView.as_view(),
            name="verification",
        ),
        path("password/", SetPasswordView.as_view(), name="password"),
        # organization account management
        path("organizatia-mea/", include(("donations.urls_ngo_account", "donations"), namespace="my-organization")),
        # old organization account management urls
        path("contul-meu/", RedirectView.as_view(pattern_name="my-organization:dashboard", permanent=True)),
        path("organizatia/", RedirectView.as_view(pattern_name="my-organization:dashboard", permanent=True)),
        path("asociatia/", RedirectView.as_view(pattern_name="my-organization:dashboard", permanent=True)),
        path("date-cont/", RedirectView.as_view(pattern_name="my-organization:settings-account", permanent=True)),
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
        path("api/ngo/upload-url/", GetUploadUrl.as_view(), name="api-ngo-upload-url"),
        path("api/ngo/form/<ngo_url>/", GetNgoForm.as_view(), name="api-ngo-form-url"),
        path("api/ngo/forms/download/", DownloadNgoForms.as_view(), name="api-ngo-forms"),
        #
        path("api/search/", SearchNgosApi.as_view(), name="api-search-ngos"),
        # Cron routes
        path("cron/ngos/remove-form/", NgoRemoveForms.as_view(), name="cron-ngo-remove-form"),
        # Django Admin
        path("admin/login/", RedirectView.as_view(pattern_name="login", permanent=True)),
        path("admin/avansat/login/", RedirectView.as_view(pattern_name="login", permanent=True)),
        path("admin/avansat/", RedirectView.as_view(pattern_name="admin:index", permanent=True)),
        path("admin/django/", RedirectView.as_view(pattern_name="admin:index", permanent=True)),
        # ADMIN HANDLERS
        path("admin/organizatii/", RedirectView.as_view(pattern_name="admin:index", permanent=True)),
        path("admin/", admin.site.urls),
        # must always be the last set of urls
        re_path(r"^(?P<ngo_url>[\w-]+)/doilasuta/", RedirectView.as_view(pattern_name="twopercent", permanent=True)),
        # re_path(r"^(?P<ngo_url>[\w-]+)/semnatura/", FormSignature.as_view(), name="ngo-twopercent-signature"),
        re_path(r"^(?P<ngo_url>[\w-]+)/succes/", RedirectionSuccessHandler.as_view(), name="ngo-twopercent-success"),
        re_path(r"^(?P<ngo_url>[\w-]+)/$", RedirectionHandler.as_view(), name="twopercent"),
        # Skip the login provider selector page and redirect to Cognito
        path(
            "allauth/login/",
            RedirectView.as_view(
                url=f'/allauth{reverse("amazon_cognito_login", urlconf="allauth.urls")}',
                permanent=True,
            ),
            name="allauth-login",
        ),
        path("allauth/", include("allauth.urls")),
        path("tinymce/", include("tinymce.urls")),
        path("robots.txt", StaticPageView.as_view(template_name="robots.txt", content_type="text/plain")),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

if settings.DEBUG:
    urlpatterns.extend(
        [
            path("email-demo/<email_path_str>/", EmailDemoHandler.as_view(), name="email-demo"),
        ]
    )

# Custom views for errors
handler400 = create_error_view(error_code=400)
handler403 = create_error_view(error_code=403)
handler404 = create_error_view(error_code=404)
handler500 = create_error_view(error_code=500)
