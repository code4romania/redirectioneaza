from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from frequent_questions.models import Question, Section


@admin.register(Section)
class SectionAdmin(ImportExportModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)

    search_fields = ("title",)
    ordering = ("order", "title")

    # save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "order",
                )
            },
        ),
    )


@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin):
    list_display = ("title", "section", "order")
    list_editable = ("order",)

    search_fields = ("title", "section__title")
    ordering = ("section__order", "section__title", "order", "title")

    #     save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "section",
                    "title",
                    "answer",
                    "order",
                ),
            },
        ),
    )
