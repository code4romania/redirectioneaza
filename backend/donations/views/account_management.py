import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.messaging import send_email
from .base import AccountHandler
from ..forms.account import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm

logger = logging.getLogger(__name__)


class ForgotPasswordHandler(AccountHandler):
    template_name = "resetare-parola.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Resetare parola"}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}

        form = ForgotPasswordForm(request.POST)
        if not form.is_valid():
            context["errors"] = form.errors
            return render(request, self.template_name, context)

        try:
            user = self.user_model.objects.get(email=form.cleaned_data["email"].lower().strip())
        except self.user_model.DoesNotExist:
            user = None

        if user:
            self._send_password_reset_email(user)

        context["found"] = _("Dacă adresa de email este validă, vei primi un email cu instrucțiuni.")

        return render(request, self.template_name, context)

    def _send_password_reset_email(self, user):
        template_context = {
            "name": user.first_name,
            "url": "{}://{}{}".format(
                self.request.scheme,
                self.request.get_host(),
                reverse(
                    "verification",
                    kwargs={
                        "verification_type": "p",
                        "user_id": user.id,
                        "signup_token": user.refresh_token(),
                    },
                ),
            ),
            "contact_mail": settings.CONTACT_EMAIL_ADDRESS,
        }
        send_email(
            subject=_("Resetare parolă redirectioneaza.ro"),
            to_emails=[user.email],
            text_template="email/reset/reset_password.txt",
            html_template="email/reset/reset_password.txt",
            context=template_context,
        )


class LoginHandler(AccountHandler):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Contul meu"}

        # if the user is logged in just redirect
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect(reverse("admin-index"))
            return redirect(reverse("contul-meu"))

        return render(request, self.template_name, context)

    def post(self, request: HttpRequest):
        context = {}

        form = LoginForm(request.POST)
        if not form.is_valid():
            context["errors"] = form.errors
            return render(request, self.template_name, context)

        email = form.cleaned_data["email"].lower().strip()
        password = form.cleaned_data["password"]

        user = authenticate(email=email, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect(reverse("admin-index"))

            return redirect(reverse("contul-meu"))

        logger.warning("Invalid email or password: {0}".format(email))
        context["email"] = email
        context["errors"] = "Se pare că această combinație de email și parolă este incorectă."

        return render(request, self.template_name, context)


class LogoutHandler(AccountHandler):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("/")


class SetPasswordHandler(AccountHandler):
    template_name = "parola-noua.html"

    def post(self, request, *args, **kwargs):
        context = {}

        form = ResetPasswordForm(request.POST)
        if not form.is_valid():
            context["errors"] = form.errors
            return render(request, self.template_name, context)

        user = request.user

        if not user:
            logger.warning("Invalid user")
            return redirect(reverse("login"))

        user.set_password(form.cleaned_data["password"])
        user.clear_token(commit=False)
        user.save()

        login(request, user)

        return redirect(reverse("contul-meu"))


class SignupHandler(AccountHandler):
    template_name = "cont-nou.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Cont nou"}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}

        form = RegisterForm(request.POST)
        if not form.is_valid():
            context["errors"] = form.errors
            return render(request, self.template_name, context)

        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        email = form.cleaned_data["email"].lower().strip()

        user = self.user_model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_verified=False,
            validation_token=uuid.uuid4(),
            token_timestamp=timezone.now(),
        )

        user.set_password(form.cleaned_data["password"])

        try:
            user.save()
        except IntegrityError:
            success = False
        else:
            success = True

        if not success:  # user_data is a tuple
            context["errors"] = "Există deja un cont cu această adresă."
            context.update({"nume": first_name, "prenume": last_name, "email": email})
            return render(request, self.template_name, context)

        token = user.refresh_token()
        verification_url = "https://{}{}".format(
            self.request.get_host(),
            reverse(
                "verification",
                kwargs={
                    "verification_type": "v",
                    "user_id": user.id,
                    "signup_token": token,
                },
            ),
        )

        template_values = {
            "name": user.last_name,
            "url": verification_url,
            "host": self.request.get_host(),
        }

        send_email(
            subject=_("Confirmare cont redirectioneaza.ro"),
            to_emails=[user.email],
            text_template="email/signup/signup_text.txt",
            html_template="email/signup/signup_inline.html",
            context=template_values,
        )

        # login the user after signup
        login(request, user)
        # redirect to my account
        return redirect(reverse("contul-meu"))


class VerificationHandler(AccountHandler):
    """handler used to:
    verify new account
    reset user password
    """

    template_name = "parola-noua.html"

    def get(self, request, *args, **kwargs):
        verification_type = kwargs["verification_type"]
        user_id = kwargs["user_id"]
        signup_token = kwargs["signup_token"]

        if verification_type not in ("p", "v"):
            raise Http404

        try:
            user = self.user_model.objects.get(pk=user_id)
        except self.user_model.DoesNotExist:
            user = None

        if not user or not user.verify_token(signup_token):
            logger.info('Could not find any user with id "%s" signup token "%s"', user_id, signup_token)
            raise Http404
        else:
            # user.clear_token()
            pass

        login(request, user)

        if verification_type == "v":
            user.is_verified = True
            user.clear_token(commit=False)
            user.save()
            return redirect(reverse("contul-meu"))

        if verification_type == "p":
            # supply user to the page
            context = {"token": signup_token, "is_admin": request.user.is_staff}
            return render(request, self.template_name, context)

        logger.info("verification type not supported")
        raise Http404
