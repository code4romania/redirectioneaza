from django.conf import settings
from django.contrib import admin
from django.core.management import call_command
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from .models import ImportJob
from .tasks.processor import process_import_task


@admin.register(ImportJob)
class ImportAdmin(admin.ModelAdmin):
    list_display = ("import_type", "csv_file", "uploaded_at", "status")
    list_filter = ("import_type", "uploaded_at")
    search_fields = ("import_type",)

    fieldsets = ((None, {"fields": ("import_type", "csv_file", "has_header")}),)

    actions = (
        "process_import",
        "transfer_logos",
        "transfer_donor_forms_dry_run",
        "transfer_donor_forms",
        "transfer_donor_forms_schedule",
    )

    @admin.action(description=_("Process the selected import jobs"))
    def process_import(self, request, queryset: QuerySet[ImportJob]):
        import_obj: ImportJob
        for import_obj in queryset:
            if settings.IMPORT_METHOD == "async":
                async_task("importer.tasks.processor.process_import_task", import_obj.id)
            else:
                process_import_task(import_obj.id)

        self.message_user(request, _("The import has been processed."))

    @admin.action(description=_("Schedule the transfer of logos to the current storage"))
    def transfer_logos(self, request, queryset: QuerySet[ImportJob]):
        call_command("import_logos", "--schedule")

        self.message_user(request, _("The logos have been transferred."))

    @admin.action(description=_("Transfer of donor forms to the current storage (dry run)"))
    def transfer_donor_forms_dry_run(self, request, queryset: QuerySet[ImportJob]):
        call_command("import_donor_forms", "--batch_size=50", "--dry_run")

        self.message_user(request, _("The donor forms have been transferred."))

    @admin.action(description=_("Transfer of donor forms to the current storage"))
    def transfer_donor_forms(self, request, queryset: QuerySet[ImportJob]):
        call_command("import_donor_forms", "--batch_size=50")

        self.message_user(request, _("The donor forms have been transferred."))

    @admin.action(description=_("Schedule the transfer of donor forms to the current storage"))
    def transfer_donor_forms_schedule(self, request, queryset: QuerySet[ImportJob]):
        call_command("import_donor_forms", "--batch_size=50", "--schedule")

        self.message_user(request, _("The donor forms have been scheduled for transfer."))
