import logging
import re
from datetime import date, datetime
from urllib.parse import urlparse

from django.conf import settings
from django.core.files import File
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from ipware import get_client_ip

from redirectioneaza.common.messaging import send_email

from ..models.main import Donor, Ngo
from ..pdf import add_signature, create_pdf
from .captcha import validate_captcha

logger = logging.getLogger(__name__)


class DonationSucces(TemplateView):
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

    def get(self, request, ngo_url, *args, **kwargs):
        context = self.get_context_data(ngo_url)
        donation_limit = date(
            year=settings.DONATIONS_LIMIT_YEAR,
            month=settings.DONATIONS_LIMIT_MONTH,
            day=settings.DONATIONS_LIMIT_DAY,
        )

        try:
            donor = Donor.objects.get(pk=request.session.get("donor_id", 0))
        except Donor.DoesNotExist:
            donor = None
        context["donor"] = donor

        context["title"] = "Donație - succes"
        context["limit"] = donation_limit

        # county = self.donor.county.lower()
        # context["anaf"] = ANAF_OFFICES.get(county, None)

        # for now, disable showing the ANAF office
        context["anaf"] = None

        # if the user didn't provide a CNP show a message
        context["has_cnp"] = request.session.get("has_cnp", False)

        return render(self.request, self.template_name, context)


class FormSignature(TemplateView):
    template_name = "signature.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ngo = None
        self.donor = None

    def get_ngo_and_donor(self, request, ngo_url):
        ngo_url = ngo_url.lower().strip()
        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            raise Http404

        try:
            donor_id = int(request.session.get("donor_id", 0))
        except ValueError:
            donor_id = 0

        if not donor_id:
            return False

        try:
            donor = Donor.objects.get(id=donor_id)
        except Donor.DoesNotExist:
            request.session.pop("donor_id", None)
            return False

        self.ngo = ngo
        self.donor = donor
        return True

    def get(self, request, ngo_url, *args, **kwargs):
        if not self.get_ngo_and_donor(request, ngo_url):
            return redirect(reverse("twopercent", kwargs={"ngo_url": ngo_url}))

        if not request.session.get("signature_required", False):
            return redirect(reverse("twopercent", kwargs={"ngo_url": ngo_url}))

        context = {
            "ngo": self.ngo,
            "title": "Donație - semnătura",
            "donor": self.donor,
        }

        return render(self.request, self.template_name, context)

    def post(self, request, ngo_url):
        if not self.get_ngo_and_donor(request, ngo_url):
            return redirect(reverse("twopercent", kwargs={"ngo_url": ngo_url}))

        signature_image = request.POST.get("signature", None)

        if not signature_image:
            return redirect(reverse("ngo-twopercent-signature", kwargs={"ngo_url": ngo_url}))

        # add the image to the PDF, retry if the file does not exist
        retries: int = 3
        while retries > 0:
            try:
                with self.donor.pdf_file.open("rb") as pdf:
                    new_pdf = add_signature(pdf.read(), signature_image)
            except ValueError as e:
                retries -= 1
                logger.warning("ValueError adding signature to PDF: %s [for donation %d]", e, self.donor.pk)
            except FileNotFoundError as e:
                retries -= 1
                logger.warning("FileNotFoundError adding signature to PDF: %s [for donation %d]", e, self.donor.pk)
            else:
                break
        else:
            logger.error("Error adding signature to PDF: %s [for donation %d]", "File not found", self.donor.pk)

            return redirect(reverse("ngo-twopercent-signature", kwargs={"ngo_url": ngo_url}))

        # delete the unsigned pdf
        self.donor.pdf_file.delete()
        self.donor.pdf_file = None

        self.donor.pdf_file.save("declaratie_semnata.pdf", File(new_pdf))
        new_pdf.close()

        send_email(
            subject=_("Formularul tău de redirecționare"),
            to_emails=[self.donor.email],
            html_template="email/signed-form/signed_form.html",
            text_template="email/signed-form/signed_form_text.txt",
            context={"form_url": self.donor.form_url},
        )
        send_email(
            subject=_("Un nou formular de redirecționare"),
            to_emails=[self.ngo.email],
            html_template="email/ngo-signed-form/signed_form.html",
            text_template="email/ngo-signed-form/signed_form_text.txt",
            context={"form_url": self.donor.form_url},
        )

        request.session.pop("signature_required", None)
        self.donor.has_signed = True

        self.donor.save()

        return redirect(reverse("ngo-twopercent-success", kwargs={"ngo_url": ngo_url}))


class TwoPercentHandler(TemplateView):
    template_name = "twopercent.html"

    def get(self, request, ngo_url, *args, **kwargs):
        try:
            ngo = Ngo.objects.get(slug=ngo_url)
        except Ngo.DoesNotExist:
            ngo = None

        # if we didn't find it or the ngo doesn't have an active page
        if ngo is None or not ngo.is_active:
            raise Http404

        # if we still have a cookie from an old session, remove it
        if "donor_id" in request.session:
            request.session.pop("donor_id", None)

        if "has_cnp" in request.session:
            request.session.pop("has_cnp", None)
            # also we can use request.session.clear(), but it might delete the logged-in user's session

        context = {
            "title": ngo.name,
            "ngo": ngo,
            "counties": settings.FORM_COUNTIES,
            "limit": settings.DONATIONS_LIMIT,
            "ngo_website_description": "",
            "ngo_website": "",
        }

        # the ngo website
        ngo_website = ngo.website if ngo.website else None
        if ngo_website:
            # try and parse the url to see if it's valid
            try:
                url_dict = urlparse(ngo_website)

                if not url_dict.scheme:
                    url_dict = url_dict._replace(scheme="http")

                # if we have a netloc, then the url is valid
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

        if not validate_captcha(request):
            errors["fields"].append("captcha")
            return self.return_error(request, ngo, errors, is_ajax)

        def get_post_value(arg, add_to_error_list=True):
            value = post.get(arg, "").strip()

            # if we received a value
            if value:
                # it should only contain alphanumeric, spaces and dash
                if re.match(r"^[\w\s.\-ăîâșț]+$", value, flags=re.I | re.UNICODE) is not None:
                    # additional validation
                    if arg == "cnp" and len(value) != 13:
                        errors["fields"].append(arg)
                        return ""

                    return value

                # the email has the @ so the first regex will fail
                elif arg == "email":
                    # if we found a match
                    email_regex = r"^[^@]+@[^@]+\.[^@]{2,}$"
                    if 5 > len(value) > 255 or re.match(email_regex, value) is None:
                        errors["fields"].append(arg)
                        return ""

                    return value

                else:
                    errors["fields"].append(arg)

            elif add_to_error_list:
                errors["fields"].append(arg)

            return ""

        donor_dict = {
            # the donor's data
            "last_name": get_post_value("nume").title(),
            "first_name": get_post_value("prenume").title(),
            "father": get_post_value("tatal").title(),
            "cnp": get_post_value("cnp", False),
            "email": get_post_value("email").lower(),
            "tel": get_post_value("tel", False),
            "street": get_post_value("strada").title(),
            "number": get_post_value("numar", False),
            # optional data
            "bl": get_post_value("bloc", False),
            "sc": get_post_value("scara", False),
            "et": get_post_value("etaj", False),
            "ap": get_post_value("ap", False),
            "city": get_post_value("localitate").title(),
            "county": get_post_value("judet"),
        }

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
            "is_social_service_viable": ngo.is_social_service_viable,
            "percent": "3,5%",
        }

        if len(errors["fields"]):
            return self.return_error(request, ngo, errors, is_ajax)

        # create the donor and save it
        donor = Donor(
            last_name=donor_dict["first_name"],
            l_name=donor_dict["last_name"],
            initial=donor_dict["father"],
            city=donor_dict["city"],
            county=donor_dict["county"],
            phone=donor_dict["tel"],
            email=donor_dict["email"],
            is_anonymous=donor_dict["anonymous"],
            income_type=donor_dict["income"],
            two_years=two_years,
            ngo=ngo,
        )

        donor.set_cnp(donor_dict["cnp"])
        donor.set_address_helper(
            street_name=donor_dict["street"],
            street_number=donor_dict["number"],
            street_bl=donor_dict["bl"],
            street_sc=donor_dict["sc"],
            street_et=donor_dict["et"],
            street_ap=donor_dict["ap"],
        )

        client_ip, _is_routable = get_client_ip(request)
        donor.geoip = {
            "ip_address": client_ip,
            "country": request.headers.get("Cloudfront-Viewer-Country", ""),
            "region": request.headers.get("Cloudfront-Viewer-Country-Region", ""),
            "city": request.headers.get("Cloudfront-Viewer-City", ""),
            "lat_long": "{},{}".format(
                request.headers.get("Cloudfront-Viewer-Latitude", ""),
                request.headers.get("Cloudfront-Viewer-Longitude", ""),
            ),
        }

        donor.save()

        pdf = create_pdf(donor_dict, ngo_data)
        donor.pdf_file.save("declaratie_nesemnata.pdf", File(pdf))

        # close the file after it has been uploaded
        pdf.close()

        donor.save()

        # set the donor id in cookie
        request.session["donor_id"] = str(donor.pk)
        request.session["has_cnp"] = bool(donor_dict["cnp"])
        request.session["signature_required"] = signature_required

        # TODO: Send the email
        if not signature_required:
            # send and email to the donor with a link to the PDF file
            send_email(
                subject=_("Formularul tău de redirecționare"),
                to_emails=[donor.email],
                html_template="email/twopercent-form/twopercent_form.html",
                text_template="email/twopercent-form/twopercent_form_text.txt",
                context={
                    "name": donor.l_name,
                    "form_url": donor.form_url,
                    "ngo": ngo,
                },
            )

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

        context = {
            "title": ngo.name,
            "ngo": ngo,
            "counties": settings.FORM_COUNTIES,
            "limit": settings.DONATIONS_LIMIT,
            "errors": errors,
        }

        now = timezone.now()
        can_donate = not now.date() > settings.DONATIONS_LIMIT

        context["can_donate"] = can_donate

        for key in self.request.POST:
            context[key] = self.request.POST[key]

        # render a response
        return render(request, self.template_name, context)


class OwnFormDownloadLinkHandler(TemplateView):
    def get(self, request, donor_date_str, donor_id, donor_hash, *args, **kwargs):
        # Don't allow downloading donation forms older than this
        cutoff_date = timezone.now() - timezone.timedelta(days=365)
        try:
            donor = Donor.objects.get(pk=donor_id, date_created__gte=cutoff_date)
        except Donor.DoesNotExist:
            raise Http404
        else:
            failed = False

        # Don't allow downloading donation forms for non active NGOs
        if not donor.ngo or not donor.ngo.is_active:
            raise Http404

        # Compare the donation date with the date string
        date_created_str = datetime.strftime(donor.date_created, "%Y%m%d")
        if date_created_str != donor_date_str:
            failed = True

        # Check the security hash
        if donor_hash != donor.donation_hash:
            failed = True

        # Check that the job has a zip file
        if not donor.pdf_file:
            failed = True

        if failed:
            raise Http404

        return redirect(donor.pdf_file.url)
