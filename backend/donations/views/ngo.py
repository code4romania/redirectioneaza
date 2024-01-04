from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from .base import BaseHandler
from ..forms import DonorInputForm
from ..models import Donor, Ngo


class DonationSucces(BaseHandler):
    template_name = "succes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ngo = Ngo.objects.get(form_url=kwargs["ngo_url"].lower())
        context["ngo"] = ngo
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        return render(self.request, self.template_name, context)


class FormSignature(BaseHandler):
    template_name = "signature.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ngo = Ngo.objects.get(form_url=kwargs["ngo_url"].lower())
        context["ngo"] = ngo
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        return redirect(reverse("ngo-twopercent-success", kwargs={"ngo_url": context["ngo_url"]}))


class TwoPercentHandler(BaseHandler):
    def get_context_data(self, request, **kwargs):
        ngo_url: str = kwargs["ngo_url"].lower()
        if not Ngo.objects.filter(form_url=ngo_url).exists():
            raise Http404("Nu exista o asociație cu acest URL")

        ngo = Ngo.objects.get(form_url=ngo_url)
        form_counties = settings.FORM_COUNTIES

        context = {"is_authenticated": False, "ngo_url": ngo_url, "ngo": ngo, "counties": form_counties}

        if request.user.is_authenticated and request.user.ngo == ngo:
            context["is_authenticated"] = True
            return context

        context["limit"] = settings.DONATIONS_LIMIT
        context["can_donate"] = True

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)

        template = "twopercent.html"

        if context["is_authenticated"]:
            template = "ngo/ngo-details.html"

        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        post = request.POST
        context = self.get_context_data(request, **kwargs)

        form = DonorInputForm(post)
        if not form.is_valid():
            context.update(form.cleaned_data)
            context["errors"] = {"fields": list(form.errors.values())}

            return render(request, "twopercent.html", context)

        new_donor: Donor = form.save(commit=False)
        new_donor.ngo = context["ngo"]

        new_donor.save()

        new_donor.pdf_url = self._generate_pdf(form.cleaned_data, context["ngo"])

        return redirect(reverse("ngo-twopercent-signature", kwargs={"ngo_url": context["ngo_url"]}))

    @staticmethod
    def _generate_pdf(donor_data, param):
        return "PDF_URL"
