import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.messaging import extend_email_context, send_email
from users.models import User

from ..forms.account import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from .base import BaseVisibleTemplateView

logger = logging.getLogger(__name__)

UserModel = get_user_model()


def django_login(request, user) -> None:
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")


class ForgotPasswordView(BaseVisibleTemplateView):
    template_name = "account/reset-password.html"
    title = _("Reset password")

    def _send_password_reset_email(self, request: HttpRequest, user: UserModel):
        verification_url = request.build_absolute_uri(
            reverse(
                "verification",
                kwargs={
                    "verification_type": "p",
                    "user_id": user.id,
                    "signup_token": user.refresh_token(),
                },
            )
        )

        template_context = {
            "first_name": user.first_name,
            "action_url": verification_url,
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        template_context.update(extend_email_context(request))

        send_email(
            subject=_("Reset redirectioneaza.ro password"),
            to_emails=[user.email],
            text_template="emails/account/reset-password/main.txt",
            html_template="emails/account/reset-password/main.html",
            context=template_context,
        )

    def _send_ngohub_notification(self, request: HttpRequest, user: UserModel):
        template_context = {
            "first_name": user.first_name,
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            "ngohub_site": settings.NGOHUB_APP_BASE,
            "action_url": reverse_lazy("allauth-login"),
        }
        template_context.update(extend_email_context(request))

        send_email(
            subject=_("Your redirectioneaza.ro account"),
            to_emails=[user.email],
            text_template="emails/account/ngohub-notification/main.txt",
            html_template="emails/account/ngohub-notification/main.html",
            context=template_context,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["captcha_public_key"] = settings.RECAPTCHA_PUBLIC_KEY
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        form = ForgotPasswordForm(request.POST)
        if not form.is_valid():
            context["form"] = form
            return render(request, self.template_name, context)

        try:
            user = self.user_model.objects.get(email=form.cleaned_data["email"].lower().strip())

            if not (user.is_ngohub_user or user.ngo and user.ngo.ngohub_org_id):
                self._send_password_reset_email(request, user)
            else:
                self._send_ngohub_notification(request, user)
        except self.user_model.DoesNotExist:
            pass

        messages.success(
            request,
            _("If the email address is valid, you will receive an email with instructions."),
        )

        return render(request, self.template_name, context)


class LoginView(BaseVisibleTemplateView):
    template_name = "account/login.html"
    title = _("Sign In")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["captcha_public_key"] = settings.RECAPTCHA_PUBLIC_KEY
        return context

    def get(self, request, *args, **kwargs):
        # if the user is logged in, then redirect
        if request.user.is_authenticated:
            if request.user.has_perm("users.can_view_old_dashboard"):
                return redirect(reverse("admin:index"))
            return redirect(reverse("my-organization:dashboard"))

        context = self.get_context_data(**kwargs)

        form = LoginForm()
        context["form"] = form

        context.update(
            {
                "ngohub_site": settings.NGOHUB_HOME_BASE,
                "account_button": _("Continue with NGO Hub"),
                "section_title": _("I have an NGO Hub account"),
                "form_action": reverse("allauth-login"),
            }
        )

        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, **kwargs):
        context = self.get_context_data(**kwargs)

        # TODO: if the account appears in NGO Hub, redirect them to the NGO Hub login page

        form = LoginForm(request.POST)
        context["form"] = form

        if not form.is_valid():
            return render(request, self.template_name, context)

        email = form.cleaned_data["email"].lower().strip()
        password = form.cleaned_data["password"]

        user: User = authenticate(email=email, password=password)
        if user is None:
            logger.warning("Invalid email or password: {0}".format(email))
            form.add_error(None, _("It seems that this email and password combination is incorrect."))

            return render(request, self.template_name, context)

        # TODO: check if the account is verified before authenticating
        django_login(request, user)

        if user.is_superuser:
            return redirect(reverse("admin:index"))
        elif user.partner:
            return redirect(reverse_lazy("admin:partners_partner_change", args=[user.partner.pk]))

        return redirect(reverse("my-organization:dashboard"))


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
            form.add_error(None, _("It seems that this email and password combination is incorrect."))
            return render(request, self.template_name, context)

        user = request.user

        if not user or user.is_anonymous:
            if not form.cleaned_data.get("token"):
                logger.warning("Invalid user")
                return redirect(reverse("login"))

            try:
                user = self.user_model.objects.get(validation_token=form.cleaned_data["token"])
            except self.user_model.DoesNotExist:
                logger.warning("Invalid user")
                return redirect(reverse("login"))

        user.set_password(form.cleaned_data["password"])
        user.clear_token(commit=False)
        user.save()

        django_login(request, user)

        return redirect(reverse("my-organization:dashboard"))


class SignupView(BaseVisibleTemplateView):
    template_name = "account/register.html"
    title = _("New account")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["captcha_public_key"] = settings.RECAPTCHA_PUBLIC_KEY
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse("my-organization:dashboard"))

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

        verification_url = request.build_absolute_uri(
            reverse(
                "verification",
                kwargs={
                    "verification_type": "v",
                    "user_id": user.id,
                    "signup_token": user.refresh_token(),
                },
            )
        )

        template_values = {
            "first_name": user.first_name,
            "action_url": verification_url,
        }
        template_values.update(extend_email_context(request))

        send_email(
            subject=_("Welcome to redirectioneaza.ro"),
            to_emails=[user.email],
            text_template="emails/account/activate-account/main.txt",
            html_template="emails/account/activate-account/main.html",
            context=template_values,
        )

        # redirect to registration confirmation page
        return redirect(reverse("signup-confirmation"))


class SignupConfirmationView(BaseVisibleTemplateView):
    template_name = "account/signup-confirmation.html"
    title = _("Account created")


class SignupVerificationView(BaseVisibleTemplateView):
    template_name = "account/signup-verification.html"
    title = _("Account verified")


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

        if verification_type == "v":
            user.is_verified = True
            user.clear_token(commit=False)
            user.save()
            return redirect(reverse("signup-verification"))

        if verification_type == "p":
            # supply user to the page
            context.update({"token": signup_token, "is_admin": request.user.is_staff})
            return render(request, self.template_name, context)

        logger.info("verification type not supported")

        raise Http404
