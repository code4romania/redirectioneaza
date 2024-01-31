from django.contrib import admin

from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        "subdomain",
        "name",
        "is_active",
    )
    list_filter = ("is_active", "date_updated")
