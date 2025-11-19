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
    ngo_fieldset: tuple[str, dict[str, tuple[str]]] = (
        _("NGO"),
        {"fields": ("ngo",)},
    )

    flags_fieldset: tuple[str, dict[str, tuple[str]]] = (
        _("Flags"),
        {
            "fields": (
                "is_main",
                "allow_online_collection",
                "visibility",
                "notifications_email",
            )
        },
    )

    form_data_fieldset: tuple[str, dict[str, tuple[str]]] = (
        _("Form Data"),
        {
            "fields": (
                "bank_account",
                "prefilled_form",
            )
        },
    )

    data_fieldset: tuple[str, dict[str, tuple[str]]] = (
        _("Data"),
        {
            "fields": (
                "name",
                "slug",
                "description",
                "display_image",
            )
        },
    )

    dates_fieldset: tuple[str, dict[str, tuple[str]]] = (
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
