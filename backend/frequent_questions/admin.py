from django.contrib import admin
from django.contrib.admin import ModelAdmin as DjangoModelAdmin
from django.db import models
from import_export.admin import ImportExportModelAdmin
from tinymce.widgets import AdminTinyMCE
from unfold.admin import ModelAdmin

from frequent_questions.models import Question, Section


@admin.register(Section)
class SectionAdmin(ImportExportModelAdmin, DjangoModelAdmin):
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
class QuestionAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = ("title", "section", "order")
    list_editable = ("order",)

    search_fields = ("title", "section__title")
    ordering = ("section__order", "section__title", "order", "title")

    formfield_overrides = {
        models.TextField: {"widget": AdminTinyMCE()},
    }

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
