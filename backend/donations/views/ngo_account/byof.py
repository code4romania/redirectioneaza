from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from donations.forms.ngo_account import BringYourOwnDataForm
from donations.models.jobs import Job
from donations.models.ngos import Ngo
from donations.views.ngo_account.common import NgoBaseListView
from users.models import User


class NgoBringYourOwnFormView(NgoBaseListView):
    template_name = "ngo-account/byof/main.html"
    title = _("Generate from external data")
    context_object_name = "archive_external"
    paginate_by = 8
    sidebar_item_target = "org-byof"

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
                "size_limit": self.file_size_limit,
                "size_limit_warning": self.file_size_warning,
                "django_form": BringYourOwnDataForm(
                    file_size_limit=self.file_size_limit, file_size_warning=self.file_size_warning
                ),
            }
        )

        return context

    def get_queryset(self):
        return Job.objects.none()

    def post(self, request: HttpRequest, *args, **kwargs):
        context = self.get_context_data()

        files = request.FILES

        form = BringYourOwnDataForm(
            request.POST,
            files=files,
            file_size_limit=self.file_size_limit,
            file_size_warning=self.file_size_warning,
        )
        if not form.is_valid():
            messages.error(request, _("There are some errors on the form."))
            return redirect(reverse("my-organization:byof"))

        messages.success(request, _("The file was uploaded successfully."))

        return redirect(reverse("my-organization:byof"))
