from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Partner


class NgoPartnerInline(admin.TabularInline):
    model = Partner.ngos.through
    extra = 1

    verbose_name = _("NGO")
    verbose_name_plural = _("NGOs")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        "subdomain",
        "name",
        "is_active",
    )
    list_filter = ("is_active", "date_updated")

    inlines = (NgoPartnerInline,)
    readonly_fields = ("date_created", "date_updated")

    fieldsets = (
        (
            _("Partner"),
            {
                "fields": (
                    "subdomain",
                    "name",
                )
            },
        ),
        (
            _("Options"),
            {
                "fields": (
                    "is_active",
                    "has_custom_header",
                    "has_custom_note",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "date_created",
                    "date_updated",
                )
            },
        ),
    )
