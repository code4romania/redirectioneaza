import logging
from typing import List

from django.conf import settings
from django.contrib import admin
from django.core.management import call_command
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import action

from donations.admin.common import CommonCauseFields
from donations.models.jobs import Job, JobStatusChoices
from donations.models.ngos import Cause, Ngo

logger = logging.getLogger(__name__)


@admin.register(Cause)
class CauseAdmin(ModelAdmin, CommonCauseFields):
    list_display = ("slug", "name", "link_to_ngo")
    list_display_links = ("name",)
    search_fields = ("name", "slug", "ngo__name")

    actions = ("generate_donations_archive",)

    fieldsets = (
        CommonCauseFields.ngo_fieldset,
        CommonCauseFields.editable_fieldset,
        CommonCauseFields.date_fieldset,
    )

    readonly_fields = CommonCauseFields.readonly_fields

    @action(description=_("Generate donations archive"))
    def generate_donations_archive(self, request, queryset: QuerySet[Cause]):
        ngo_names: List[str] = []

        for cause in queryset:
            ngo = cause.ngo
            new_job: Job = Job(ngo=ngo, cause=cause, owner=request.user)
            new_job.save()

            try:
                if settings.FORMS_DOWNLOAD_METHOD == "async":
                    call_command("download_donations", new_job.id)
                else:
                    call_command("download_donations", new_job.id, "--run")

                ngo_names.append(f"{ngo.id} - {ngo.name}")
            except Exception as e:
                logger.error(e)

                new_job.status = JobStatusChoices.ERROR
                new_job.save()

        if ngo_names:
            message = _("The donations archive has been generated for the following NGOs: ") + ", ".join(ngo_names)
        else:
            message = _("The donations archive could not be generated for any of the selected NGOs.")

        self.message_user(request, message)

    @admin.display(description=_("NGO"))
    def link_to_ngo(self, obj: Cause):
        ngo: Ngo = obj.ngo

        link_url = reverse("admin:donations_ngo_change", args=(ngo.pk,))
        return format_html(f'<a href="{link_url}">{ngo.name}</a>')
