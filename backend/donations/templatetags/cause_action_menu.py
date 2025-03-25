from typing import Any, Dict, List

from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Cause

register = template.Library()


@register.filter
def dropdown(cause: Cause) -> List[Dict[str, Any]]:
    link = ""
    if is_active := (cause is not None):
        link = reverse("my-organization:cause", kwargs={"cause_id": cause.pk})

    return [
        {
            "title": _("Edit cause"),
            "active": is_active,
            "link": link,
        },
    ]


@register.filter
def button_disabled(cause: Cause) -> bool:
    if not cause:
        return True
    return False


@register.filter
def button_title(cause: Cause) -> str:
    if not cause:
        return _("Cause doesn't exist")
    return _("Form options")
