from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from redirectioneaza.common.admin import HasNgoFilter
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "email",
    )
    list_display_links = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser", HasNgoFilter)

    search_fields = ("email", "first_name", "last_name")
    autocomplete_fields = ("ngo",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "ngo",
                    "is_active",
                    "is_verified",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "date_joined",
                    "last_login",
                    "token_timestamp",
                )
            },
        ),
    )

    readonly_fields = ("password", "old_password", "date_joined", "last_login", "token_timestamp")
