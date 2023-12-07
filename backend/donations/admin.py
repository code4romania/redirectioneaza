from django.contrib import admin

from .models import Ngo, Donor


@admin.register(Ngo)
class NgoAdmin(admin.ModelAdmin):
    list_display = ("id", "registration_number", "name")
    list_display_links = ("registration_number", "name")


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "ngo")
    list_display_links = ("email",)
    list_filter = ("date_created",)
