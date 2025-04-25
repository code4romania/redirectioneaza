from django.contrib import admin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from donations.admin.common import span_internal
from donations.models import Ngo
from donations.models.downloads import RedirectionsDownloadJob


@admin.register(RedirectionsDownloadJob)
class DownloadJobAdmin(ModelAdmin):
    list_display = ("id", "link_to_ngo", "status", "date_created")
    list_display_links = ("id", "status", "date_created")
    list_filter = ("date_created", "status")

    readonly_fields = ("date_created",)
    autocomplete_fields = ("ngo",)

    fieldsets = (
        (
            _("NGO"),
            {"fields": ("ngo",)},
        ),
        (
            _("Status"),
            {"fields": ("status",)},
        ),
        (
            _("Data"),
            {
                "fields": (
                    "queryset",
                    "output_rows",
                    "output_file",
                )
            },
        ),
        (
            _("Date"),
            {
                "fields": (
                    "date_created",
                    "date_finished",
                )
            },
        ),
    )

    @admin.display(description=_("NGO"))
    def link_to_ngo(self, obj: RedirectionsDownloadJob):
        ngo: Ngo = obj.ngo

        link_url = reverse_lazy("admin:donations_ngo_change", args=(ngo.pk,))
        return span_internal(href=link_url, content=ngo.name)
