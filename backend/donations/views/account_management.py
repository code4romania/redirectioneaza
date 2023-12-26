import logging
import uuid

from django.contrib.auth import login, logout
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone


from .base import AccountHandler


logger = logging.getLogger(__name__)


class ForgotPasswordHandler(AccountHandler):
    pass


class LoginHandler(AccountHandler):
    pass


class LogoutHandler(AccountHandler):
    def get(self, request):
        logout(request)
        return redirect("/")


class SetPasswordHandler(AccountHandler):
    pass


class SignupHandler(AccountHandler):
    template_name = "cont-nou.html"

    def get(self, request, *args, **kwargs):
        context = {}
        context["title"] = "Cont nou"
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}
        post = self.request.POST

        # TODO: Create a sign up form with validations
        first_name = post.get("nume")
        last_name = post.get("prenume")

        email = post.get("email")
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

        user = self.user_model(
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
                'verification',
                kwargs={
                    "verification_type": "v",
                    "user_id": user.id,
                    "signup_token": token,
                }
            )
        )

        template_values = {
            "name": user.last_name,
            "url": verification_url,
            "host": self.request.get_host(),
        }

        html_body = render_to_string("email/signup/signup_inline.html", context=template_values)
        text_body = render_to_string("email/signup/signup_text.txt", context=template_values)

        message = EmailMultiAlternatives(
            "Confirmare cont redirectioneaza.ro",
            text_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)

        # login the user after signup
        login(request, user)
        # redirect to my account
        return redirect(reverse("contul-meu"))


class VerificationHandler(AccountHandler):
    """handler used to:
            verify new account
            reset user password
    """

    template_name = 'parola-noua.html'

    def get(self, request, verification_type, user_id, signup_token):
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

        if verification_type == 'v':
            user.is_verified = True
            user.clear_token(commit=False)
            user.save()
            return redirect(reverse("contul-meu"))

        elif verification_type == 'p':
            # supply user to the page
            self.template_values.update({
                "token": signup_token
            })
            context = {}
            context["token"] = signup_token
            context["is_admin"] = request.user.is_staff
            return render(request, self.template_name, context)
        else:
            logger.info('verification type not supported')
            raise Http404

