from django.conf import settings
from django.contrib import admin
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from .models import ImportJob
from .tasks import process_import_task


@admin.register(ImportJob)
class ImportAdmin(admin.ModelAdmin):
    list_display = ("import_type", "csv_file", "uploaded_at", "status")
    list_filter = ("import_type", "uploaded_at")
    search_fields = ("import_type",)

    fieldsets = ((None, {"fields": ("import_type", "csv_file", "has_header")}),)

    actions = ("process_import",)

    @admin.action(description=_("Process the selected import jobs"))
    def process_import(self, request, queryset: QuerySet[ImportJob]):
        import_obj: ImportJob
        for import_obj in queryset:
            if settings.IMPORT_METHOD == "async":
                async_task("importer.tasks.process_import_task", import_obj.id)
            else:
                process_import_task(import_obj.id)

        self.message_user(request, _("The import has been processed."))
