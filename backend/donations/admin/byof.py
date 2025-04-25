from django.contrib import admin
from unfold.admin import ModelAdmin

from donations.models.byof import OwnFormsUpload


@admin.register(OwnFormsUpload)
class OwnFormsUploadAdmin(ModelAdmin):
    list_display = ("id", "ngo", "status", "date_created")
    list_display_links = ("id", "ngo")
    list_filter = ("date_created", "status")

    readonly_fields = ("date_created",)
    autocomplete_fields = ("ngo",)
