from typing import Any, Dict, List

from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Cause

register = template.Library()


@register.filter
def dropdown(cause: Cause) -> List[Dict[str, Any]]:
    link = ""
    if is_active := cause.slug:
        link = reverse("twopercent", kwargs={"ngo_url": cause.slug})

    return [
        {
            "title": _("Do a thing"),
            "active": is_active,
            "link": link,
        },
    ]


@register.filter
def button_disabled(cause: Cause) -> bool:
    return not cause.is_main


@register.filter
def button_title(cause: Cause) -> str:
    if cause.is_main:
        return _("Form options")
    return _("Downloads are disabled for unsigned redirections")
