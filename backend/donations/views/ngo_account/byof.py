from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from donations.forms.ngo_account import BringYourOwnDataForm
from donations.models.ngos import Ngo
from donations.models.byof import OwnFormsUpload
from donations.views.download_donations.byof import handle_external_data_processing
from donations.views.ngo_account.common import NgoBaseListView
from users.models import User


class NgoBringYourOwnFormView(NgoBaseListView):
    template_name = "ngo-account/byof/main.html"
    title = _("Generate from external data")
    context_object_name = "archive_external"
    paginate_by = 8
    tab_title = "external"
    sidebar_item_target = "org-byof"
    context_object_name = "archive_jobs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user: User = self.request.user
        ngo: Ngo = user.ngo if user.ngo else None

        context.update(
            {
                "user": user,
                "ngo": ngo,
                "title": self.title,
                "active_tab": self.tab_title,
                "size_limit": 2 * settings.MEBIBYTE,
                "size_limit_warning": _("File size must not exceed {mb} MB").format(mb=2),
                "django_form": BringYourOwnDataForm(),
            }
        )

        return context

    def get_queryset(self):
        return OwnFormsUpload.objects.filter(ngo=self.request.user.ngo).select_related("ngo").order_by("-date_created")

    @method_decorator(login_required(login_url=reverse_lazy("login")))
    def post(self, request: HttpRequest, *args, **kwargs):
        user: User = request.user

        ngo: Ngo = user.ngo if user.ngo else None
        if not ngo:
            messages.error(request, _("You need to add your NGO's information first."))
            return redirect(reverse_lazy("my-organization:presentation"))

        form = BringYourOwnDataForm(request.POST, request.FILES)

        if not form.is_valid():
            error_values = list(form.errors.values())
            all_errors = []
            for error_list in error_values:
                all_errors.extend(error_list)
            messages.error(request, ", ".join(all_errors))
            return redirect(reverse("my-organization:byof"))

        own_upload = form.save(commit=False)
        own_upload.ngo = ngo
        own_upload.save()

        async_task(handle_external_data_processing, own_upload.pk)

        messages.success(request, _("The uploaded data file will be processed soon."))

        return redirect(reverse("my-organization:byof"))
