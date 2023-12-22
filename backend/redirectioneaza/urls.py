"""
URL configuration for the redirectioneaza project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin as django_admin, admin
from django.urls import path, re_path

from donations.views.account_management import (
    ForgotPasswordHandler,
    LoginHandler,
    LogoutHandler,
    SetPasswordHandler,
    SignupHandler,
    VerificationHandler,
)
from donations.views.admin import (
    AdminHome,
    AdminNewNgoHandler,
    AdminNgoHandler,
    AdminNgosList,
    SendCampaign,
    UserAccounts,
)
from donations.views.api import CheckNgoUrl, GetNgoForm, GetNgoForms, GetUploadUrl, NgosApi, Webhook
from donations.views.cron import CustomExport, NgoExport, NgoRemoveForms, Stats
from donations.views.my_account import MyAccountDetailsHandler, MyAccountHandler, NgoDetailsHandler
from donations.views.site import AboutHandler, ForNgoHandler, HomePage, NoteHandler, PolicyHandler, TermsHandler


admin.site.site_header = f"Admin | {settings.VERSION_SUFFIX}"


urlpatterns = (
    [
        # the public part of the app
        path("", HomePage.as_view(), name="home"),
        path("ong/", ForNgoHandler.as_view()),
        # backup in case of old urls. to be removed
        path("pentru-ong-uri/", ForNgoHandler.as_view()),
        # path("asociatii", NgoListHandler.as_view()),  # TODO
        path("termeni/", TermsHandler.as_view()),
        path("TERMENI/", TermsHandler.as_view()),
        path("nota-de-informare/", NoteHandler.as_view(), name="note"),
        path("politica/", PolicyHandler.as_view()),
        path("despre/", AboutHandler.as_view()),
        # account management
        path("cont-nou", SignupHandler.as_view()),
        #
        #
        # TODO: all the URLs below this line
        #
        path("login", LoginHandler.as_view(), name="login"),
        path("logout", LogoutHandler.as_view(), name="logout"),
        path("forgot", ForgotPasswordHandler.as_view(), name="forgot"),
        # verification url: used for signup, and reset password
        re_path(
            "(?P<type>[v|p])/<int:user_id>-<str:signup_token>",
            VerificationHandler.as_view(),
            name="verification",
        ),
        path("password", SetPasswordHandler.as_view()),
        # my account
        path("contul-meu", MyAccountHandler.as_view(), name="contul-meu"),
        path("asociatia", NgoDetailsHandler.as_view(), name="asociatia"),
        path("date-cont", MyAccountDetailsHandler.as_view(), name="date-contul-meu"),
        path(
            "api/ngo/check-url/<ngo_url>",
            CheckNgoUrl.as_view(),
            name="api-ngo-check-url",
        ),
        path("api/ngo/upload-url", GetUploadUrl.as_view(), name="api-ngo-upload-url"),
        path("api/ngo/form/<ngo_url>", GetNgoForm.as_view(), name="api-ngo-form-url"),
        path("api/ngo/forms/download", GetNgoForms.as_view(), name="api-ngo-forms"),
        path("api/ngos", NgosApi.as_view(), name="api-ngos"),
        path("webhook", Webhook.as_view(), name="webhook"),
        # ADMIN HANDLERS
        path("admin/organizatii", AdminNgosList.as_view(), name="admin-ngos"),
        path("admin/conturi", UserAccounts.as_view(), name="admin-users"),
        path("admin/campanii", SendCampaign.as_view(), name="admin-campanii"),
        path("admin/ong-nou", AdminNewNgoHandler.as_view(), name="admin-ong-nou"),
        path("admin/<ngo_url>", AdminNgoHandler.as_view(), name="admin-ong"),
        path("admin", AdminHome.as_view(), name="admin"),
        # TODO: Check the ngo_url parameter format because it currently captures too much
        # path("<ngo_url>", TwoPercentHandler.as_view(), name="twopercent"),
        # path(
        #     "<ngo_url>/semnatura",
        #     FormSignature.as_view(),
        #     name="ngo-twopercent-signature",
        # ),
        # path(
        #     "<ngo_url>/succes", DonationSucces.as_view(), name="ngo-twopercent-success"
        # ),
        # path("<ngo_url>/doilasuta", NgoHandler.as_view(), name="ngo-url"),
        # Cron routes
        path("cron/stats", Stats.as_view()),
        path("cron/ngos/remove-form", NgoRemoveForms.as_view(), name="ngo-remove-form"),
        path("cron/ngos/export", NgoExport.as_view()),
        path("cron/export/custom", CustomExport.as_view()),
        # Django Admin
        path("django-admin/", django_admin.site.urls),
    ]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
