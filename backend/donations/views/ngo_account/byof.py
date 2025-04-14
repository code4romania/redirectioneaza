from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from donations.forms.ngo_account import BringYourOwnDataForm
from donations.models.ngos import Ngo
from donations.views.download_donations.byof import generate_xml_from_external_data
from donations.views.ngo_account.common import NgoBaseListView
from users.models import User


class NgoBringYourOwnFormView(NgoBaseListView):
    template_name = "ngo-account/byof/main.html"
    title = _("Generate from external data")
    context_object_name = "archive_external"
    paginate_by = 8
    sidebar_item_target = "org-byof"

    file_allowed_types = ["text/csv"]  # , "application/vnd.ms-excel"]
    file_size_limit = 2 * settings.MEBIBYTE
    file_size_warning = _("File size must not exceed 2 MB")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "allowed_types": self.file_allowed_types,
                "size_limit": self.file_size_limit,
                "size_limit_warning": self.file_size_warning,
                "django_form": BringYourOwnDataForm(
                    file_allowed_types=self.file_allowed_types,
                    file_size_limit=self.file_size_limit,
                    file_size_warning=self.file_size_warning,
                ),
            }
        )

        return context

    def get_queryset(self):
        return []

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request: HttpRequest, *args, **kwargs):
        files = request.FILES

        post = request.POST
        user: User = request.user

        ngo: Ngo = user.ngo if user.ngo else None
        if not ngo:
            messages.error(request, _("You need to add your NGO's information first."))
            return redirect(reverse_lazy("my-organization:presentation"))

        form = BringYourOwnDataForm(
            post,
            files=files,
            file_allowed_types=self.file_allowed_types,
            file_size_limit=self.file_size_limit,
            file_size_warning=self.file_size_warning,
        )

        if not form.is_valid():
            messages.error(request, _("There are some errors on the form."))
            return redirect(reverse("my-organization:byof"))

        result = generate_xml_from_external_data(
            ngo=ngo,
            iban=form.cleaned_data["bank_account"],
            file=form.cleaned_data["upload_file"],
        )

        if "error" in result:
            messages.error(request, result["error"])
            return redirect(reverse("my-organization:byof"))

        messages.success(request, _("The file was uploaded successfully."))

        return redirect(reverse("my-organization:byof"))
