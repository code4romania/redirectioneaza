import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.core.files import File
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from ipware import get_client_ip

from redirectioneaza.common.messaging import extend_email_context, send_email
from .base import BaseVisibleTemplateView
from .common.misc import get_ngo_cause
from ..forms.redirection import DonationForm
from ..models.donors import Donor
from ..pdf import create_full_pdf

logger = logging.getLogger(__name__)


class RedirectionSuccessHandler(BaseVisibleTemplateView):
    template_name = "form/success/main.html"
    title = _("Successful redirection")

    def get_context_data(self, ngo_url, **kwargs):
        context = super().get_context_data(**kwargs)

        cause_url = ngo_url.lower().strip()
        cause, ngo = get_ngo_cause(cause_url)

        if not cause and not ngo:
            raise Http404("NGO not found")

        try:
            request = self.request
            donor = Donor.objects.get(pk=request.session.get("donor_id", 0))
        except Donor.DoesNotExist:
            donor = None

        context.update(
            {
                "donor": donor,
                "limit": settings.DONATIONS_LIMIT,
            }
        )

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if not context["donor"] and not settings.DEBUG:
            return redirect(reverse("twopercent", kwargs={"ngo_url": kwargs["ngo_url"]}))

        return self.render_to_response(context)


class RedirectionHandler(TemplateView):
    template_name = "form/redirection.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request
        ngo_url = kwargs.get("ngo_url", "")

        cause, ngo = get_ngo_cause(ngo_url)

        # if we didn't find it or the ngo doesn't have an active page
        if (cause is None or not cause.ngo.can_receive_forms()) and (ngo is None or not ngo.can_receive_forms()):
            raise Http404

        absolute_path = request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": ngo_url}))

        context.update(
            {
                "title": cause.name if cause else ngo.name,
                "cause": cause,
                "ngo": ngo,
                "absolute_path": absolute_path,
            }
        )

        # if we still have a cookie from an old session, remove it
        if "donor_id" in request.session:
            request.session.pop("donor_id", None)

        if "has_cnp" in request.session:
            request.session.pop("has_cnp", None)
            # also we can use request.session.clear(), but it might delete the logged-in user's session

        now = timezone.now()
        is_donation_period_active = not now.date() > settings.DONATIONS_LIMIT
        donation_status = "open" if is_donation_period_active else "closed"

        context.update(
            {
                "donation_status": donation_status,
                "is_admin": request.user.is_staff,
                "limit": settings.DONATIONS_LIMIT,
                "month_limit": settings.DONATIONS_LIMIT_MONTH_NAME,
            }
        )
        if donation_status == "closed":
            return context

        ngo_website_description = ""
        ngo_website = cause.ngo.website if cause.ngo.website else ""

        if ngo_website:
            # try and parse the url to see if it's valid
            try:
                url_dict = urlparse(ngo_website)

                if not url_dict.scheme:
                    url_dict = url_dict._replace(scheme="http")

                # if we have a netloc, then the URL is valid
                # use the netloc as the website name
                if url_dict.netloc:
                    ngo_website_description = url_dict.netloc
                    ngo_website = url_dict.geturl()

                # of we don't have the netloc, when parsing the url
                # urlparse might send it to path
                # move that to netloc and remove the path
                elif url_dict.path:
                    url_dict = url_dict._replace(netloc=url_dict.path)
                    ngo_website_description = url_dict.path

                    url_dict = url_dict._replace(path="")

                    ngo_website = url_dict.geturl()
                else:
                    raise

            except Exception:
                ngo_website = None

        context.update(
            {
                "counties": settings.FORM_COUNTIES_WITH_SECTORS,
                "captcha_public_key": settings.RECAPTCHA_PUBLIC_KEY,
                "ngo_website_description": ngo_website_description,
                "ngo_website": ngo_website,
            }
        )

        return context

    def post(self, request, ngo_url):
        post = self.request.POST

        (
            cause,
            ngo,
        ) = get_ngo_cause(ngo_url)

        if not cause and not ngo:
            raise Http404

        # if we have an ajax request, return an answer
        is_ajax = post.get("ajax", False)

        form = DonationForm(post)
        if not form.is_valid():
            messages.error(request, _("There are some errors on the redirection form."))
            return self.return_error(request, form, is_ajax, ngo_url=ngo_url)

        signature: str = form.cleaned_data["signature"]

        new_donor = Donor(
            f_name=form.cleaned_data["f_name"],
            l_name=form.cleaned_data["l_name"],
            initial=form.cleaned_data["initial"],
            email=form.cleaned_data["email_address"],
            phone=form.cleaned_data["phone_number"],
            is_anonymous=form.cleaned_data["agree_contact"],
            two_years=form.cleaned_data["two_years"],
            anaf_gdpr=form.cleaned_data["anaf_gdpr"],
            city=form.cleaned_data["locality"],
            county=form.cleaned_data["county"],
            has_signed=signature is not None and signature != "",
            income_type="wage",
            cause=cause,
            ngo=ngo,
        )
        new_donor.set_cnp(form.cleaned_data["cnp"])
        new_donor.set_address_helper(
            street_name=form.cleaned_data["street_name"],
            street_number=form.cleaned_data["street_number"],
            street_bl=form.cleaned_data["flat"],
            street_sc=form.cleaned_data["entrance"],
            street_et=form.cleaned_data["floor"],
            street_ap=form.cleaned_data["apartment"],
        )

        # create the donor and save it

        client_ip, _is_routable = get_client_ip(request)
        new_donor.geoip = {
            "ip_address": client_ip,
            "country": request.headers.get("Cloudfront-Viewer-Country", ""),
            "region": request.headers.get("Cloudfront-Viewer-Country-Region", ""),
            "city": request.headers.get("Cloudfront-Viewer-City", ""),
            "lat_long": "{},{}".format(
                request.headers.get("Cloudfront-Viewer-Latitude", ""),
                request.headers.get("Cloudfront-Viewer-Longitude", ""),
            ),
        }

        new_donor.save()

        pdf = create_full_pdf(new_donor, signature)
        new_donor.pdf_file.save("formular.pdf", File(pdf))

        # close the file after it has been uploaded
        pdf.close()

        new_donor.save()

        # set the donor id in cookie
        request.session["donor_id"] = str(new_donor.pk)

        mail_context = {"action_url": request.build_absolute_uri(new_donor.form_url)}
        mail_context.update(extend_email_context(request))

        donor_email_context = mail_context.copy()
        donor_email_context.update(
            {
                "ngo_url": request.build_absolute_uri(reverse("twopercent", kwargs={"ngo_url": ngo_url})),
                "ngo_name": ngo.name,
                "donation_is_two_years": new_donor.two_years,
            }
        )

        # TODO: add a text for two-year donations
        # send and email to the donor with a link to the PDF file
        if signature:
            send_email(
                subject=_("Un nou formular de redirecționare"),
                to_emails=[ngo.email],
                html_template="emails/ngo/new-form-received/main.html",
                text_template="emails/ngo/new-form-received/main.txt",
                context=mail_context,
            )
            send_email(
                subject=_("Formularul tău de redirecționare"),
                to_emails=[new_donor.email],
                html_template="emails/donor/redirection-with-signature/main.html",
                text_template="emails/donor/redirection-with-signature/main.txt",
                context=donor_email_context,
            )
        else:
            ngo_address = ngo.address
            if ngo.locality:
                ngo_address += f", {ngo.locality}"
            if ngo.county:
                ngo_address += f", {ngo.county}"

            donor_email_context.update(
                {
                    "ngo_address": ngo_address,
                    "ngo_email": ngo.email,
                }
            )
            send_email(
                subject=_("Formularul tău de redirecționare"),
                to_emails=[new_donor.email],
                html_template="emails/donor/redirection-sans-signature/main.html",
                text_template="emails/donor/redirection-sans-signature/main.txt",
                context=donor_email_context,
            )

        url = reverse("ngo-twopercent-success", kwargs={"ngo_url": ngo_url})

        # if not an ajax request, redirect
        if is_ajax:
            response = {"url": url}
            return JsonResponse(response)
        else:
            return redirect(url)

    def return_error(self, request, form, is_ajax, ngo_url):
        if is_ajax:
            return JsonResponse(form.errors)

        context = self.get_context_data(ngo_url=ngo_url)
        context.update({"redirection_form": form})

        for key in self.request.POST:
            context[key] = self.request.POST[key]

        # render a response
        return render(request, self.template_name, context)


class OwnFormDownloadLinkHandler(TemplateView):
    def get(self, request, donor_date_str, donor_id, donor_hash, *args, **kwargs):
        # Don't allow downloading donation forms older than this
        cutoff_date = timezone.now() - timedelta(days=365)
        try:
            donor = Donor.objects.get(pk=donor_id, date_created__gte=cutoff_date)
        except Donor.DoesNotExist:
            raise Http404
        else:
            failed = False

        # Don't allow downloading donation forms for inactive NGOs
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
