import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.messaging import send_email

from ..forms.account import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from .base import BaseVisibleTemplateView

logger = logging.getLogger(__name__)

UserModel = get_user_model()


def django_login(request, user) -> None:
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")


class ForgotPasswordView(BaseVisibleTemplateView):
    template_name = "account/reset-password.html"
    title = _("Reset password")

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

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

        context["found"] = _("If the email address is valid, you will receive an email with instructions.")

        return render(request, self.template_name, context)

    def _send_password_reset_email(self, user: UserModel):
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
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        send_email(
            subject=_("Reset redirectioneaza.ro password"),
            to_emails=[user.email],
            text_template="email/reset/reset_password.txt",
            html_template="email/reset/reset_password.html",
            context=template_context,
        )


class LoginView(BaseVisibleTemplateView):
    template_name = "account/login.html"
    title = _("Sign In")

    def get(self, request, *args, **kwargs):
        # if the user is logged in, then redirect
        if request.user.is_authenticated:
            if request.user.has_perm("users.can_view_old_dashboard"):
                return redirect(reverse("admin-index"))
            return redirect(reverse("contul-meu"))

        context = self.get_context_data(**kwargs)

        context.update(
            {
                "ngohub_site": settings.NGOHUB_HOME_BASE,
                "account_button": _("Continue with NGO Hub"),
                "section_title": _("I have an NGO Hub account"),
                "form_action": reverse("amazon_cognito_login"),
            }
        )

        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, **kwargs):
        context = self.get_context_data(**kwargs)

        # TODO: if the account appears in NGO Hub, redirect them to the NGO Hub login page

        form = LoginForm(request.POST)
        if not form.is_valid():
            context["errors"] = form.errors
            return render(request, self.template_name, context)

        email = form.cleaned_data["email"].lower().strip()
        password = form.cleaned_data["password"]

        user = authenticate(email=email, password=password)
        if user is not None:
            django_login(request, user)
            if user.has_perm("users.can_view_old_dashboard"):
                return redirect(reverse("admin-index"))

            return redirect(reverse("contul-meu"))
        else:
            # Check the old password authentication and migrate it to the new method
            user_model = get_user_model()
            try:
                user = user_model.objects.get(email=email)
            except user_model.DoesNotExist:
                user = None

            if user and user.check_old_password(password):
                user.set_password(password)
                user.save()
                django_login(request, user)
                if user.has_perm("users.can_view_old_dashboard"):
                    return redirect(reverse("admin-index"))
                return redirect(reverse("contul-meu"))

        logger.warning("Invalid email or password: {0}".format(email))
        context["email"] = email
        context["errors"] = _("It seems that this email and password combination is incorrect.")

        return render(request, self.template_name, context)


class LogoutView(BaseVisibleTemplateView):
    title = _("Sign Out")

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("/")


class SetPasswordView(BaseVisibleTemplateView):
    template_name = "account/set-password.html"
    title = _("Set New Password")

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

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

        django_login(request, user)

        return redirect(reverse("contul-meu"))


class SignupView(BaseVisibleTemplateView):
    template_name = "account/register.html"
    title = _("New account")

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("contul-meu"))

        context = self.get_context_data(**kwargs)

        context.update(
            {
                "ngohub_site": settings.NGOHUB_HOME_BASE,
                "account_button": _("Register new account"),
                "account_button_is_external": True,
                "section_title": _("Register through NGO Hub"),
                "form_action": settings.NGOHUB_APP_BASE,
            }
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = RegisterForm(request.POST)
        if not form.is_valid():
            context["errors"] = form.errors
            context["errors"].pop("__all__", None)
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
            subject=_("Welcome to redirectioneaza.ro"),
            to_emails=[user.email],
            text_template="email/signup/signup_text.txt",
            html_template="email/signup/signup_inline.html",
            context=template_values,
        )

        # login the user after signup
        django_login(request, user)

        # redirect to my account
        return redirect(reverse("contul-meu"))


class VerificationView(BaseVisibleTemplateView):
    """
    handler used to:
        v - verify new account
        p - reset user password
    """

    template_name = "account/set-password.html"
    title = _("Verification")

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

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

        django_login(request, user)

        if verification_type == "v":
            user.is_verified = True
            user.clear_token(commit=False)
            user.save()
            return redirect(reverse("contul-meu"))

        if verification_type == "p":
            # supply user to the page
            context.update({"token": signup_token, "is_admin": request.user.is_staff})
            return render(request, self.template_name, context)

        logger.info("verification type not supported")

        raise Http404
