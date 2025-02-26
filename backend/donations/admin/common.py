from typing import Dict, Tuple

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


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

    def get_readonly_fields(self, request: HttpRequest, obj=None):
        if obj and not obj.is_accepting_forms:
            return self.readonly_fields + ("allow_online_collection",)

        return self.readonly_fields
