from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator

from ..models import Ngo
from .base import AccountHandler


class MyAccountDetailsHandler(AccountHandler):
    pass


@method_decorator(login_required, name="get")
class MyAccountHandler(AccountHandler):
    template_name = "ngo/my-account.html"

    def get(self, request, *args, **kwargs):
        context = {
            "user": request.user,
            "ngo": request.user.ngo if request.user.ngo else None,
        }
        return render(request, self.template_name, context)


class NgoDetailsHandler(AccountHandler):
    template_name = "ngo/ngo-details.html"

    def get(self, request, *args, **kwargs):
        context = {
            "user": request.user,
            "ngo": request.user.ngo if request.user.ngo else None,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        post = request.POST

        ngo: Ngo = request.user.ngo

        if not ngo:
            ngo = Ngo()
            ngo.save()

            ngo.is_verified = False
            ngo.is_active = True

            request.user.ngo = ngo
            request.user.save()

        ngo.name = post.get("ong-nume")
        ngo.description = post.get("ong-descriere")
        ngo.phone = post.get("ong-tel")
        ngo.email = post.get("ong-email")
        ngo.website = post.get("ong-website")
        ngo.address = post.get("ong-adresa")
        ngo.county = post.get("ong-judet")
        ngo.active_region = post.get("ong-activitate")
        ngo.form_url = post.get("ong-url")
        ngo.registration_number = post.get("ong-cif")
        ngo.bank_account = post.get("ong-cont")
        ngo.has_special_status = True if post.get("special-status") == "on" else False
        ngo.is_accepting_forms = True if post.get("accepts-forms") == "on" else False
        ngo.logo_url = post.get("ong-logo-url", "")
        ngo.image_url = post.get("ong-logo")
        ngo.other_emails = ""

        ngo.save()

        context = {
            "user": request.user,
            "ngo": request.user.ngo if request.user.ngo else None,
        }

        return render(request, self.template_name, context)
