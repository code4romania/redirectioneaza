from django.contrib import admin

from .models import Ngo, Donor
from django.utils.translation import gettext_lazy as _


@admin.register(Ngo)
class NgoAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "name")
    list_display_links = ("registration_number", "name")


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "ngo")
    list_display_links = ("email",)
    list_filter = ("date_created",)

    exclude = ("personal_identifier",)

    fieldsets = (
        (
            _("NGO"),
            {"fields": ("ngo",)},
        ),
        (
            _("Identity"),
            {"fields": ("first_name", "last_name", "initial", "county", "city", "email", "phone")},
        ),
        (
            _("Info"),
            {"fields": ("is_anonymous", "income_type", "two_years")},
        ),
        (
            _("File"),
            {"fields": ("pdf_url", "filename", "has_signed")},
        ),
        (
            _("Date"),
            {"fields": ("date_created",)},
        ),
    )
    readonly_fields = ("date_created",)
