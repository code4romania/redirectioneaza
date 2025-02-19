from django.contrib import admin
from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group as BaseGroup
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from redirectioneaza.common.admin import HasNgoFilter
from .models import GroupProxy, User

# Remove the default admins for User and Group
try:
    admin.site.unregister(User)
except NotRegistered:
    pass

try:
    admin.site.unregister(BaseGroup)
except NotRegistered:
    pass


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        "pk",
        "email",
        "is_verified",
        "date_updated",
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
                    "is_ngohub_user",
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

    readonly_fields = ("password", "date_joined", "last_login", "token_timestamp")


@admin.register(GroupProxy)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
