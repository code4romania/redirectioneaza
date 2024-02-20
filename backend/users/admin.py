from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "email",
    )
    list_display_links = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser")
