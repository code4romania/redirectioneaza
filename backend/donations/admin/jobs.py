from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from donations.models.jobs import Job


@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = ("id", "ngo", "status", "date_created")
    list_display_links = ("id", "ngo")
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
            _("File"),
            {"fields": ("zip",)},
        ),
        (
            _("Date"),
            {"fields": ("date_created",)},
        ),
    )
