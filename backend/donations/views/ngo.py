from datetime import date

from django.conf import settings
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .base import BaseHandler
from ..forms import DonorInputForm
from ..models import Donor, Ngo


class DonationSucces(BaseHandler):
    template_name = "succes.html"

    def get_context_data(self, ngo_url, **kwargs):
        context = super().get_context_data(**kwargs)

        ngo_url = ngo_url.lower().strip()
        try:
            ngo = Ngo.objects.get(form_url=ngo_url)
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
        # self.template_values["anaf"] = ANAF_OFFICES.get(county, None)

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
            ngo = Ngo.objects.get(form_url=ngo_url)
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
    def get_context_data(self, request: HttpRequest, ngo_url: str):
        ngo_url = ngo_url.lower().strip()

        try:
            ngo = Ngo.objects.get(form_url=ngo_url)
        except Ngo.DoesNotExist:
            raise Http404("Nu exista o asociație cu acest URL")

        form_counties = settings.FORM_COUNTIES

        context = {"is_authenticated": False, "ngo_url": ngo_url, "ngo": ngo, "counties": form_counties}

        if request.user.is_authenticated and request.user.ngo == ngo:
            context["is_authenticated"] = True
            return context

        context["limit"] = settings.DONATIONS_LIMIT
        context["can_donate"] = True

        return context

    def get(self, request, ngo_url):
        context = self.get_context_data(request, ngo_url)

        template = "twopercent.html"

        if context["is_authenticated"]:
            template = "ngo/ngo-details.html"

        return render(request, template, context)

    def post(self, request, ngo_url):
        post = request.POST

        context = self.get_context_data(request, ngo_url)

        ngo = context["ngo"]
        is_ajax = post.get("ajax", False)

        # TODO: Captcha

        # if the ngo accepts online forms
        signature_required = False
        if ngo.is_accepting_forms:
            wants_to_sign = post.get("wants-to-sign", False)
            if wants_to_sign == "True":
                signature_required = True

        form = DonorInputForm(post)
        if not form.is_valid():
            context.update(form.cleaned_data)
            context["errors"] = {"fields": list(form.errors.values())}

            if is_ajax:
                return JsonResponse(context["errors"])
            else:
                return render(request, "twopercent.html", context)

        donor: Donor = form.save(commit=False)
        donor.ngo = ngo
        donor.save()

        request.session["donor_id"] = donor.pk
        request.session["has_cnp"] = form.cleaned_data.get("cnp", "")
        request.session["signature_required"] = signature_required

        # TODO: really create the PDF
        donor.pdf_url = self._generate_pdf(form.cleaned_data, context["ngo"])
        donor.save()

        if not signature_required:
            # send and email to the donor with a link to the PDF file

            # TODO: Send the actual email
            # self.send_email("twopercent-form", donor, self.ngo)
            pass

        url = reverse("ngo-twopercent-success", kwargs={"ngo_url": ngo_url})
        if signature_required:
            url = reverse("ngo-twopercent-signature", kwargs={"ngo_url": ngo_url})

        # if not an ajax request, redirect
        if is_ajax:
            response = {"url": url}
            return JsonResponse(response)
        else:
            return redirect(url)

    @staticmethod
    def _generate_pdf(donor_data, param):
        # TODO: really create the PDF
        return "PDF_URL"
