import logging
from typing import List

from django.contrib import admin
from django.core.management import call_command
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from redirectioneaza.common.admin import HasNgoFilter
from users.models import User
from .models.jobs import Job, JobStatusChoices
from .models.main import Donor, Ngo
from .workers.update_organization import update_organization

logger = logging.getLogger(__name__)


class NgoPartnerInline(admin.TabularInline):
    # noinspection PyUnresolvedReferences
    model = Ngo.partners.through
    extra = 1

    autocomplete_fields = ("partner",)


class NgoUserInline(admin.StackedInline):
    # noinspection PyUnresolvedReferences
    model = User
    extra = 0

    readonly_fields = ("link_to_user", "email", "first_name", "last_name", "is_active", "is_staff", "is_superuser")

    fieldsets = (
        (
            _("User Link"),
            {"fields": ("link_to_user",)},
        ),
        (
            _("User Details"),
            {"fields": ("email", "first_name", "last_name")},
        ),
        (
            _("User Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
    )

    def has_add_permission(self, request, obj):
        return False

    @admin.display(description=_("User"))
    def link_to_user(self, obj: User):
        link_url = reverse("admin:users_user_change", args=(obj.pk,))
        return format_html(f'<a href="{link_url}">{obj.email}</a>')


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
class NgoAdmin(ModelAdmin):
    list_display = ("id", "ngohub_org_id", "slug", "registration_number", "name")
    list_display_links = ("id", "ngohub_org_id", "slug", "registration_number", "name")
    list_filter = (
        "date_created",
        "is_verified",
        "is_active",
        "is_accepting_forms",
        "partners",
        HasOwnerFilter,
        "county",
        "active_region",
        "registration_number_valid",
    )
    list_per_page = 30

    search_fields = ("name", "registration_number", "slug", "description")

    inlines = (NgoPartnerInline, NgoUserInline)

    readonly_fields = ("date_created", "date_updated", "get_donations_link")

    actions = (
        "generate_donations_archive",
        "clean_registration_numbers",
        "update_from_ngohub_sync",
        "update_from_ngohub_async",
    )

    fieldsets = (
        (
            _("Donations"),
            {"fields": ("get_donations_link",)},
        ),
        (
            _("NGO"),
            {"fields": ("slug", "name", "registration_number", "description")},
        ),
        (
            _("Activity"),
            {
                "fields": (
                    "is_verified",
                    "is_active",
                    "is_accepting_forms",
                    "is_social_service_viable",
                )
            },
        ),
        (
            _("Logo"),
            {"fields": ("logo",)},
        ),
        (
            _("Contact"),
            {
                "fields": (
                    "address",
                    "county",
                    "active_region",
                    "phone",
                    "website",
                    "email",
                )
            },
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

    @admin.display(description=_("Donations"))
    def get_donations_link(self, obj: Ngo):
        link_name = _("Open the NGO donor list")
        link_url = reverse("admin:donations_donor_changelist")
        return format_html(
            f'<a data-popup="yes" id="ngo_donor_list" class="related-widget-wrapper-link" href="{link_url}?ngo_id={obj.id}&_popup=1" target="_blank">{link_name}</a>'
        )

    @admin.action(description=_("Generate donations archive"))
    def generate_donations_archive(self, request, queryset: QuerySet[Ngo]):
        ngo_names: List[str] = []

        for ngo in queryset:
            new_job: Job = Job(ngo=ngo, owner=request.user)
            new_job.save()

            try:
                call_command("download_donations", new_job.id)

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

    @admin.action(description=_("Clean up registration numbers"))
    def clean_registration_numbers(self, request, queryset: QuerySet[Ngo]):
        result = call_command("registration_numbers_cleanup")

        if result:
            self.message_user(request, result, level="ERROR")
        else:
            self.message_user(request, _("Registration numbers are clean."), level="SUCCESS")

    @admin.action(description=_("Update from NGO Hub synchronously"))
    def update_from_ngohub_sync(self, request, queryset: QuerySet[Ngo]):
        for ngo in queryset:
            update_organization(ngo.id, update_method="sync")

        self.message_user(request, _("NGOs updated from NGO Hub."))

    @admin.action(description=_("Update from NGO Hub asynchronously"))
    def update_from_ngohub_async(self, request, queryset: QuerySet[Ngo]):
        for ngo in queryset:
            update_organization(ngo.id, update_method="async")

        self.message_user(request, _("NGOs are being updated from NGO Hub."))


@admin.register(Donor)
class DonorAdmin(ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "ngo", "date_created")
    list_display_links = ("id", "email", "first_name", "last_name")
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
                    "first_name",
                    "last_name",
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
