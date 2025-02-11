from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from .models import Partner


class NgoPartnerInline(TabularInline):
    model = Partner.ngos.through
    extra = 1

    verbose_name = _("NGO")
    verbose_name_plural = _("NGOs")

    autocomplete_fields = ("ngo",)


@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    list_display = (
        "subdomain",
        "name",
        "is_active",
    )
    list_filter = (
        "is_active",
        "date_updated",
        "has_custom_header",
        "has_custom_note",
    )
    search_fields = (
        "subdomain",
        "name",
    )

    inlines = (NgoPartnerInline,)
    readonly_fields = (
        "date_created",
        "date_updated",
    )

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
                    "display_ordering",
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
