from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from donations.models.donors import Donor
from redirectioneaza.common.admin import HasNgoFilter


@admin.register(Donor)
class DonorAdmin(ModelAdmin):
    list_display = ("id", "email", "l_name", "f_name", "ngo", "cause", "has_signed", "date_created")
    list_display_links = ("id", "email", "l_name", "f_name")
    list_filter = (
        "date_created",
        HasNgoFilter,
        "is_anonymous",
        "has_signed",
        "two_years",
        "income_type",
    )
    date_hierarchy = "date_created"

    search_fields = ("email", "ngo__name", "ngo__slug")

    exclude = ("encrypted_cnp", "encrypted_address")

    readonly_fields = ("date_created", "get_form_url")
    autocomplete_fields = ("ngo",)

    fieldsets = (
        (
            _("NGO"),
            {"fields": ("ngo",)},
        ),
        (
            _("Identity"),
            {
                "fields": (
                    "l_name",
                    "f_name",
                    "initial",
                    "county",
                    "city",
                    "email",
                    "phone",
                )
            },
        ),
        (
            _("Info"),
            {"fields": ("is_anonymous", "income_type", "two_years")},
        ),
        (
            _("File"),
            {"fields": ("has_signed", "pdf_file", "get_form_url")},
        ),
        (
            _("Date"),
            {"fields": ("date_created", "geoip")},
        ),
    )

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Form"))
    def get_form_url(self, obj: Donor):
        return obj.form_url
