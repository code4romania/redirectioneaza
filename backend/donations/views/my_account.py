from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, QuerySet
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.http import Http404

from .base import AccountHandler
from ..models.main import Donor, Ngo


class MyAccountDetailsHandler(AccountHandler):
    template_name = "ngo/my-account-details.html"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        context = {"user": request.user}
        return render(request, self.template_name, context)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST

        request.user.last_name = post.get("nume")
        request.user.first_name = post.get("prenume")

        request.user.save()

        context = {"user": request.user}

        return render(request, self.template_name, context)


class MyAccountHandler(AccountHandler):
    template_name = "ngo/my-account.html"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user_ngo: Ngo = request.user.ngo if request.user.ngo else None
        donors: QuerySet[Donor] = Donor.objects.filter(Q(ngo=user_ngo)).order_by("-date_created")

        years = range(timezone.now().year, settings.START_YEAR, -1)

        grouped_donors = OrderedDict()
        for donor in donors:
            index = donor.date_created.year
            if index in years:
                if index not in grouped_donors:
                    grouped_donors[index] = []
                grouped_donors[index].append(donor)

        context = {
            "user": request.user,
            "limit": settings.DONATIONS_LIMIT,
            "ngo": user_ngo,
            "donors": grouped_donors,
            "counties": settings.FORM_COUNTIES,
        }
        return render(request, self.template_name, context)


class NgoDetailsHandler(AccountHandler):
    template_name = "ngo/ngo-details.html"

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_superuser:
            return redirect(reverse("admin-ngos"))

        if not user.is_authenticated or not user.ngo:
            return redirect(reverse("contul-meu"))

        context = {
            "title": "Date asociație",
            "user": user,
            "ngo": user.ngo if user.ngo else None,
            "counties": settings.FORM_COUNTIES,
        }

        return render(request, self.template_name, context)

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request, *args, **kwargs):
        post = request.POST
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied()

        if user.is_superuser:
            ngo_url = post.get("old-ong-url", "")

            try:
                user.ngo = Ngo.objects.get(slug=ngo_url)
            except Ngo.DoesNotExist:
                raise Http404()

        ngo: Ngo = user.ngo

        is_new_ngo = False
        if not ngo:
            is_new_ngo = True

            ngo = Ngo()

            ngo.is_verified = False
            ngo.is_active = True

        ngo.name = post.get("ong-nume")
        ngo.description = post.get("ong-descriere")
        ngo.phone = post.get("ong-tel")
        ngo.email = post.get("ong-email")
        ngo.website = post.get("ong-website")
        ngo.address = post.get("ong-adresa")
        ngo.county = post.get("ong-judet")
        ngo.active_region = post.get("ong-activitate")
        ngo.slug = post.get("ong-url").lower()
        ngo.registration_number = post.get("ong-cif")
        ngo.bank_account = post.get("ong-cont")
        ngo.has_special_status = True if post.get("special-status") == "on" else False
        ngo.is_accepting_forms = True if post.get("accepts-forms") == "on" else False

        ngo.other_emails = ""

        if request.user.is_superuser:
            ngo.is_verified = post.get("ong-verificat") == "on"
            ngo.is_active = post.get("ong-activ") == "on"

        ## TODO: more admin changes

        #     # if we want to change the url
        #     if ong_url != ngo.key.id():

        #         is_ngo_url_available = check_ngo_url(ong_url)
        #         if is_ngo_url_available == False:
        #             self.template_values["errors"] = url_taken
        #             self.render()
        #             return

        #         new_key = Key(NgoEntity, ong_url)

        #         # replace all the donors key
        #         donors = Donor.query(Donor.ngo == ngo.key).fetch()
        #         if donors:
        #             for donor in donors:
        #                 donor.ngo = new_key
        #                 donor.put()

        #         # replace the users key
        #         ngos_user = User.query(Donor.ngo == ngo.key).get()
        #         if ngos_user:
        #             ngos_user.ngo = new_key
        #             ngos_user.put()

        #         # copy the old model
        #         new_ngo = ngo
        #         # delete the old model
        #         ngo.key.delete()
        #         # add a new key
        #         new_ngo.key = new_key

        #         ngo = new_ngo

        #     if new_owner:
        #         new_owner = User.query(User.email == new_owner).get()
        #         if new_owner:
        #             # delete the associtation between the old account and the NGO
        #             old_user = User.query(User.ngo == ngo.key).get()
        #             old_user.ngo = None
        #             new_owner.ngo = ngo.key

        #             old_user.put()
        #             new_owner.put()
        #         else:
        #             self.template_values["errors"] = no_new_owner
        #             self.render()
        #             return

        ngo.save()

        if is_new_ngo:
            user.ngo = ngo
            user.save()
            if request.user.is_superuser:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))
            else:
                return redirect(reverse("contul-meu"))

        else:
            if request.user.is_superuser:
                return redirect(reverse("admin-ong", kwargs={"ngo_url": user.ngo.slug}))
            else:
                return redirect(reverse("association"))
