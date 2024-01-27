import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.messaging import send_email
from .base import AccountHandler

logger = logging.getLogger(__name__)


class ForgotPasswordHandler(AccountHandler):
    template_name = "resetare-parola.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Resetare parola"}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        post = self.request.POST

        email = post.get("email")

        if not email:
            context["errors"] = _("Câmpul email nu poate fi gol.")
            return render(request, self.template_name, context)

        ## TODO: Fix captcha
        # captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)
        #
        # # if the captcha is not valid return
        # if not captcha_response.is_valid:
        #     context["errors"] = _(
        #         "Se pare că a fost o problemă cu verificarea reCAPTCHA. Te rugăm să încerci din nou."
        #     )
        #     return render(request, self.template_name, context)

        try:
            user = self.user_model.objects.get(email=email)
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

    def post(self, request):
        email = request.POST.get("email", "").lower().strip()
        password = request.POST.get("parola", "")

        context = {}

        if not email:
            context["errors"] = "Câmpul email nu poate fi gol."
            return render(request, self.template_name, context)

        if not password:
            context["errors"] = "Câmpul parola nu poate fi gol."
            return render(request, self.template_name, context)

        ## TODO: Fix captcha
        # captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)

        # # if the captcha is not valid return
        # if not captcha_response.is_valid:
        #     context["errors"] = (
        #         "Se pare că a fost o problemă cu verificarea reCAPTCHA." + "Te rugăm să încerci din nou."
        #     )
        #     return render(request, self.template_name, context)

        user = authenticate(email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse("contul-meu"))
        else:
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
        post = self.request.POST

        password = post.get("parola")
        password_confirm = post.get("confirma-parola")

        if not password:
            context["errors"] = "Câmpul parola nu poate fi gol."
            return render(request, self.template_name, context)

        if not password_confirm:
            context["errors"] = "Câmpul parola confirmare nu poate fi gol."
            return render(request, self.template_name, context)

        if password != password_confirm:
            context["errors"] = "Parolele nu se potrivesc."
            return render(request, self.template_name, context)

        user = request.user

        if not user:
            logger.warning("Invalid user")
            return redirect(reverse("login"))

        user.set_password(password)
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
        post = self.request.POST

        # TODO: Create a sign up form with validations
        first_name = post.get("nume")
        last_name = post.get("prenume")

        email = post.get("email", "").lower().strip()
        password = post.get("parola")

        if not first_name:
            context["errors"] = "Câmpul nume nu poate fi gol."
            return render(request, self.template_name, context)

        if not last_name:
            context["errors"] = "Câmpul prenume nu poate fi gol."
            return render(request, self.template_name, context)

        if not email:
            context["errors"] = "Câmpul email nu poate fi gol."
            return render(request, self.template_name, context)

        if not password:
            context["errors"] = "Câmpul parola nu poate fi gol."
            return render(request, self.template_name, context)

        # TODO: fix captcha
        # captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, post.remote_addr)

        # # if the captcha is not valid return
        # if not captcha_response.is_valid:
        #     context["errors"] = "Se pare că a fost o problemă cu verificarea reCAPTCHA. Te rugăm să încerci din nou."
        #     return render(request, self.template_name, context)

        user = self.user_model.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_verified=False,
            validation_token=uuid.uuid4(),
            token_timestamp=timezone.now(),
        )

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
            user.clear_token()

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
