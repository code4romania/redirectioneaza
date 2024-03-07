from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.admin import HasNgoFilter
from .models.jobs import Job
from .models.main import Donor, Ngo
from users.models import User


class NgoPartnerInline(admin.TabularInline):
    # noinspection PyUnresolvedReferences
    model = Ngo.partners.through
    extra = 1

    autocomplete_fields = ("partner",)


class NgoUserInline(admin.StackedInline):
    # noinspection PyUnresolvedReferences
    model = User
    extra = 0

    readonly_fields = ("link_to_user",)

    fieldsets = (
        (
            _("Link"),
            {"fields": ("link_to_user",)},
        ),
        (
            _("User"),
            {"fields": ("email", "first_name", "last_name")},
        ),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
    )

    def has_add_permission(self, request, obj):
        return False

    @admin.display(description=_("User"))
    def link_to_user(self, obj: User):
        # TODO: use reverse for this
        return format_html(f'<a href="/admin/django/users/user/{obj.id}/change/">{obj.email}</a>')


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
        "is_accepting_forms",
        "partners",
        HasOwnerFilter,
        "county",
        "active_region",
    )
    list_per_page = 30

    search_fields = ("name", "registration_number", "slug", "description")

    inlines = (NgoPartnerInline, NgoUserInline)

    readonly_fields = ("date_created", "date_updated")

    fieldsets = (
        (
            _("NGO"),
            {"fields": ("slug", "name", "registration_number", "description")},
        ),
        (
            _("Activity"),
            {"fields": ("is_verified", "is_active", "is_accepting_forms", "has_special_status")},
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
            _("Details"),
            {"fields": ("bank_account", "prefilled_form")},
        ),
        (
            _("Date"),
            {"fields": ("date_created", "date_updated")},
        ),
    )

    @admin.display(description=_("Users"))
    def get_users(self, obj):
        return ", ".join([user.email for user in obj.users.all()])


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "ngo", "date_created")
    list_display_links = ("email",)
    list_filter = ("date_created", HasNgoFilter, "is_anonymous", "income_type", "two_years")

    exclude = ("personal_identifier", "address")

    readonly_fields = ("date_created",)
    autocomplete_fields = ("ngo",)

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

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
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
