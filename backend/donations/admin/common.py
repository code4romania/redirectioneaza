from typing import Dict, Tuple

from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


def span_icon(href: str, content: str, icon: str) -> str:
    icon_span = f"""<span class="material-symbols-outlined">{icon}</span>"""
    icon_and_text = f"""<span class="flex flex-row gap-2 items-center">{icon_span} {content}</span>"""
    anchor = f"""<a href="{href}" target="_blank">{icon_and_text}</a>"""
    return format_html(anchor)


def span_external(href: str, content: str) -> str:
    return span_icon(href=href, content=content, icon="open_in_new")


def span_internal(href: str, content: str) -> str:
    return span_icon(href=href, content=content, icon="ungroup")


class CommonCauseFields:
    ngo_fieldset: Tuple[str, Dict[str, Tuple[str]]] = (
        _("NGO"),
        {"fields": ("ngo",)},
    )

    editable_fieldset: Tuple[str, Dict[str, Tuple[str]]] = (
        _("Cause"),
        {
            "fields": (
                "allow_online_collection",
                "name",
                "slug",
                "description",
                "bank_account",
                "display_image",
            )
        },
    )

    date_fieldset: Tuple[str, Dict[str, Tuple[str]]] = (
        _("Date"),
        {
            "fields": (
                "date_created",
                "date_updated",
            )
        },
    )

    readonly_fields = ("ngo", "date_created", "date_updated")

    def get_readonly_fields(self, _: HttpRequest, obj=None):
        if obj and not obj.is_accepting_forms:
            return self.readonly_fields + ("allow_online_collection",)

        return self.readonly_fields
