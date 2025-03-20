from typing import Any, Dict, List

from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def redirection_dropdown(redirection: Dict) -> List[Dict[str, Any]]:
    link = ""
    if is_active := redirection["has_signed"]:
        link = reverse("my-organization:redirection-download-link", args=[redirection["id"]])

    return [
        {
            "title": _("Download form"),
            "active": is_active,
            "link": link,
        },
    ]


@register.filter
def button_disabled(redirection: Dict) -> bool:
    return not redirection["has_signed"]


@register.filter
def button_title(redirection: Dict) -> str:
    if redirection["has_signed"]:
        return _("Form options")
    return _("Downloads are disabled for unsigned redirections")
