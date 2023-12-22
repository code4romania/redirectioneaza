import uuid

from django.contrib.auth import login
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone


from .base import AccountHandler


class ForgotPasswordHandler(AccountHandler):
    pass


class LoginHandler(AccountHandler):
    pass


class LogoutHandler(AccountHandler):
    pass


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

        # TODO: Send the email
        # self.send_email("signup", user)
        # XXX: We switch to Django's email sender

        send_mail(
            "Confirmare cont redirectioneaza.ro",
            "Here is the message.",
            "from@example.com",
            ["to@example.com"],
            fail_silently=False,
        )

        # login the user after signup
        login(request, user)
        # redirect to my account
        return redirect(reverse("contul-meu"))


class VerificationHandler(AccountHandler):
    pass
