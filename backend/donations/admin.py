from django.contrib import admin

from redirectioneaza.common.admin import HasNgoFilter
from .models.jobs import Job
from .models.main import Ngo, Donor
from django.utils.translation import gettext_lazy as _


class NgoPartnerInline(admin.TabularInline):
    model = Ngo.partners.through
    extra = 1


class HasOwnerFilter(admin.SimpleListFilter):
    title = _("Has owner")
    parameter_name = "has_owner"

    def lookups(self, request, model_admin):
        return ("yes", _("Yes")), ("no", _("No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(users__isnull=False)
        if self.value() == "no":
            return queryset.filter(users__isnull=True)


@admin.register(Ngo)
class NgoAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "registration_number", "name")
    list_display_links = ("registration_number", "name")
    list_filter = (
        "date_created",
        "is_verified",
        "is_active",
        "partners",
        HasOwnerFilter,
        "county",
        "active_region",
    )

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

    readonly_fields = ("date_created",)

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
            {"fields": ("pdf_url", "filename", "has_signed", "pdf_file")},
        ),
        (
            _("Date"),
            {"fields": ("date_created",)},
        ),
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "ngo", "status", "date_created")
    list_display_links = ("id", "ngo")
    list_filter = ("date_created", "status")

    readonly_fields = ("date_created",)

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
