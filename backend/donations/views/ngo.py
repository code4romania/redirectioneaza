import re
from datetime import date
from hashlib import sha1
from urllib.parse import urlparse

from django.conf import settings
from django.core.files import File
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .base import BaseHandler
from ..models.main import Donor, Ngo
from ..pdf import create_pdf


class DonationSucces(BaseHandler):
    template_name = "succes.html"

    def get_context_data(self, ngo_url, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo_url = ngo_url.lower().strip()
        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            ngo = None

        context["ngo"] = ngo
        return context

    def get(self, request, ngo_url):
        context = self.get_context_data(ngo_url)
        DONATION_LIMIT = date(timezone.now().year, 5, 25)

        try:
            donor = Donor.objects.get(pk=request.session.get("donor_id", 0))
        except Donor.DoesNotExist:
            donor = None
        context["donor"] = donor

        context["title"] = "Donație - succes"
        context["limit"] = DONATION_LIMIT

        # county = self.donor.county.lower()
        # context["anaf"] = ANAF_OFFICES.get(county, None)

        # for now, disable showing the ANAF office
        context["anaf"] = None

        # if the user didn't provide a CNP show a message
        context["has_cnp"] = request.session.get("has_cnp", False)

        return render(self.request, self.template_name, context)


class FormSignature(BaseHandler):
    template_name = "signature.html"

    def get_context_data(self, ngo_url, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo_url = ngo_url.lower().strip()
        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            ngo = None

        context["ngo"] = ngo
        return context

    def get(self, request, ngo_url):
        context = self.get_context_data(ngo_url)

        return render(self.request, self.template_name, context)

    def post(self, request, ngo_url):
        # context = self.get_context_data(ngo_url)

        return redirect(reverse("ngo-twopercent-success", kwargs={"ngo_url": ngo_url}))


class TwoPercentHandler(BaseHandler):
    template_name = "twopercent.html"

    def get(self, request, ngo_url):
        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            ngo = None

        # if we didn't find it or the ngo doesn't have an active page
        if ngo is None or not ngo.is_active:
            raise Http404

        # if we still have a cookie from an old session, remove it
        if "donor_id" in request.session:
            request.session.pop("donor_id")

        if "has_cnp" in request.session:
            request.session.pop("has_cnp")
            # also we can use request.session.clear(), but it might delete the logged in user's session

        context = {}
        context["title"] = ngo.name
        # make sure the ngo shows a logo
        ngo.logo_url = ngo.logo_url if ngo.logo_url else settings.DEFAULT_NGO_LOGO
        context["ngo"] = ngo
        context["counties"] = settings.LIST_OF_COUNTIES
        context["limit"] = settings.DONATIONS_LIMIT

        # the ngo website
        ngo_website = ngo.website if ngo.website else None
        if ngo_website:
            # try and parse the the url to see if it's valid
            try:
                url_dict = urlparse(ngo_website)

                if not url_dict.scheme:
                    url_dict = url_dict._replace(scheme="http")

                # if we have a netloc, than the url is valid
                # use the netloc as the website name
                if url_dict.netloc:
                    context["ngo_website_description"] = url_dict.netloc
                    context["ngo_website"] = url_dict.geturl()

                # of we don't have the netloc, when parsing the url
                # urlparse might send it to path
                # move that to netloc and remove the path
                elif url_dict.path:
                    url_dict = url_dict._replace(netloc=url_dict.path)
                    context["ngo_website_description"] = url_dict.path

                    url_dict = url_dict._replace(path="")

                    context["ngo_website"] = url_dict.geturl()
                else:
                    raise

            except Exception:
                context["ngo_website"] = None
        else:
            context["ngo_website"] = None

        now = timezone.now()
        can_donate = not now.date() > settings.DONATIONS_LIMIT

        context["can_donate"] = can_donate
        context["is_admin"] = request.user.is_staff  # TODO: check this

        return render(request, self.template_name, context)

    def post(self, request, ngo_url):
        post = self.request.POST
        errors = {"fields": [], "server": False}

        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            raise Http404

        # if we have an ajax request, just return an answer
        is_ajax = post.get("ajax", False)

        def get_post_value(arg, add_to_error_list=True):
            value = post.get(arg)

            # if we received a value
            if value:
                # it should only contains alpha numeric, spaces and dash
                if re.match(r"^[\w\s.\-ăîâșț]+$", value, flags=re.I | re.UNICODE) is not None:
                    # additional validation
                    if arg == "cnp" and len(value) != 13:
                        errors["fields"].append(arg)
                        return ""

                    return value

                # the email has the @ so the first regex will fail
                elif arg == "email":
                    # if we found a match
                    if re.match(r"[^@]+@[^@]+\.[^@]+", value) is not None:
                        return value

                    errors["fields"].append(arg)
                    return ""

                else:
                    errors["fields"].append(arg)

            elif add_to_error_list:
                errors["fields"].append(arg)

            return ""

        donor_dict = {}

        # the donor's data
        donor_dict["first_name"] = get_post_value("nume").title()
        donor_dict["last_name"] = get_post_value("prenume").title()
        donor_dict["father"] = get_post_value("tatal").title()
        donor_dict["cnp"] = get_post_value("cnp", False)

        donor_dict["email"] = get_post_value("email").lower()
        donor_dict["tel"] = get_post_value("tel", False)

        donor_dict["street"] = get_post_value("strada").title()
        donor_dict["number"] = get_post_value("numar", False)

        # optional data
        donor_dict["bl"] = get_post_value("bloc", False)
        donor_dict["sc"] = get_post_value("scara", False)
        donor_dict["et"] = get_post_value("etaj", False)
        donor_dict["ap"] = get_post_value("ap", False)

        donor_dict["city"] = get_post_value("localitate").title()
        donor_dict["county"] = get_post_value("judet")

        # if the user wants to redirect for 2 years
        two_years = post.get("two-years") == "on"

        # if the ngo accepts online forms
        signature_required = False
        if ngo.is_accepting_forms:
            wants_to_sign = post.get("wants-to-sign", False)
            if wants_to_sign == "True":
                signature_required = True

        # if he would like the ngo to see the donation
        donor_dict["anonymous"] = post.get("anonim") != "on"

        # what kind of income does he have: wage or other
        donor_dict["income"] = post.get("income", "wage")

        # the ngo data
        ngo_data = {
            "name": ngo.name,
            "account": ngo.bank_account.upper(),
            "cif": ngo.registration_number,
            "two_years": two_years,
            "special_status": ngo.has_special_status,
            "percent": "3,5%",
        }

        if len(errors["fields"]):
            return self.return_error(request, ngo, errors, is_ajax)

        ## TODO: Captcha check
        # captcha_response = submit(post.get(CAPTCHA_POST_PARAM), CAPTCHA_PRIVATE_KEY, self.request.remote_addr)

        # # if the captcha is not valid return
        # if not captcha_response.is_valid:

        #     errors["fields"].append("codul captcha")
        #     self.return_error(errors)
        #     return

        # TODO
        # the user's folder name, it's just his md5 hashed db id
        # user_folder = security.hash_password('123', "md5")
        user_folder = "123123"

        # a way to create unique file names
        # get the local time in iso format
        # run that through SHA1 hash
        # output a hex string
        filename = "{0}/{1}/{2}.pdf".format(
            settings.USER_FORMS, str(user_folder), sha1(timezone.now().isoformat().encode("utf8")).hexdigest()
        )

        pdf = create_pdf(donor_dict, ngo_data)

        # create the donor and save it
        donor = Donor(
            first_name=donor_dict["first_name"],
            last_name=donor_dict["last_name"],
            city=donor_dict["city"],
            county=donor_dict["county"],
            email=donor_dict["email"],
            phone=donor_dict["tel"],
            is_anonymous=donor_dict["anonymous"],
            two_years=two_years,
            income_type=donor_dict["income"],
            ## TODO:
            # make a request to get geo ip data for this user
            # geoip = self.get_geoip_data(),
            ngo=ngo,
            filename=filename,
        )
        donor.save()

        donor.pdf_file.save(filename, File(pdf))

        # close the file after it has been uploaded
        pdf.close()

        # TODO: Get rid of pdf_url
        donor.pdf_url = donor.pdf_file.url
        donor.save()

        # set the donor id in cookie
        request.session["donor_id"] = str(donor.pk)
        request.session["has_cnp"] = bool(donor_dict["cnp"])
        request.session["signature_required"] = signature_required

        # TODO: Send the email
        # if not signature_required:
        #     # send and email to the donor with a link to the PDF file
        #     self.send_email("twopercent-form", donor, ngo)

        url = reverse("ngo-twopercent-success", kwargs={"ngo_url": ngo_url})
        if signature_required:
            url = reverse("ngo-twopercent-signature", kwargs={"ngo_url": ngo_url})

        # if not an ajax request, redirect
        if is_ajax:
            response = {"url": url}
            return JsonResponse(response)
        else:
            return redirect(url)

    def return_error(self, request, ngo, errors, is_ajax):
        if is_ajax:
            return JsonResponse(errors)

        context = {}
        context["title"] = ngo.name
        # make sure the ngo shows a logo
        ngo.logo = ngo.logo if ngo.logo else settings.DEFAULT_NGO_LOGO
        context["ngo"] = ngo
        context["counties"] = settings.LIST_OF_COUNTIES
        context["limit"] = settings.DONATIONS_LIMIT

        context["errors"] = errors

        now = timezone.now()
        can_donate = not now.date() > settings.DONATIONS_LIMIT

        context["can_donate"] = can_donate

        for key in self.request.POST:
            context[key] = self.request.POST[key]

        # render a response
        return render(request, self.template_name, context)
