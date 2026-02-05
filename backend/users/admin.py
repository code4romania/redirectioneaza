import codecs
import csv

from django.contrib import admin
from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group as BaseGroup
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from utils.common.admin import HasNgoFilter

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
        "email",
        "is_active",
        "is_verified",
        "is_ngohub_user",
        "date_updated",
    )
    list_display_links = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser", "is_ngohub_user", HasNgoFilter)

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

    def get_urls(self):
        return [
            path(
                "export/",
                self.admin_site.admin_view(self.export_users),
                name="export-users",
            ),
            *super().get_urls(),
        ]

    def export_users(self, request):
        if not request.user.has_perm("users.view_user"):
            raise PermissionDenied

        try:
            users = User.export_users(
                who_has_ngo=request.GET.get("ngo"),
                who_is_verified=request.GET.get("verified"),
                who_is_ngohub_user=request.GET.get("ngohub"),
            )
        except ValidationError as e:
            return HttpResponse(e.message)

        filename = "users_export_{}.csv".format(timezone.now())

        response = HttpResponse(
            content_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
        )
        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response, dialect=csv.excel)
        for user in users:
            writer.writerow(user)

        return response


@admin.register(GroupProxy)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
