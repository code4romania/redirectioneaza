from django.contrib import admin

from redirectioneaza.common.admin import HasNgoFilter
from .models.main import Ngo, Donor
from django.utils.translation import gettext_lazy as _


class NgoPartnerInline(admin.TabularInline):
    model = Ngo.partners.through
    extra = 1


@admin.register(Ngo)
class NgoAdmin(admin.ModelAdmin):
    list_display = ("id", "registration_number", "name")
    list_display_links = ("registration_number", "name")
    list_filter = ("date_created", "is_verified", "is_active", "county", "active_region")

    search_fields = ("name", "registration_number", "slug")

    inlines = (NgoPartnerInline,)

    readonly_fields = ("date_created",)

    fieldsets = (
        (
            _("NGO"),
            {"fields": ("slug", "name", "registration_number", "description", "is_verified", "is_active")},
        ),
        (
            _("Logo"),
            {"fields": ("logo", "logo_url")},
        ),
        (
            _("Contact"),
            {"fields": ("address", "county", "active_region", "phone", "website", "email")},
        ),
        (
            _("Bank"),
            {"fields": ("bank_account",)},
        ),
        (
            _("Date"),
            {"fields": ("date_created",)},
        ),
    )


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "ngo", "date_created")
    list_display_links = ("email",)
    list_filter = ("date_created", HasNgoFilter, "is_anonymous", "income_type", "two_years")

    exclude = ("personal_identifier", "address")

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
