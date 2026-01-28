from typing import Any

from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

register = template.Library()


def _build_download_button(redirection: dict) -> dict[str, Any]:
    download_link: str = ""
    if is_active := redirection["has_signed"]:
        download_link = reverse("my-organization:redirection-download-link", args=[redirection["id"]])

    return {
        "title": _("Download form"),
        "active": is_active,
        "link": download_link,
    }


def _build_disable_button(redirection: dict) -> dict[str, Any]:
    disable_link: str = ""
    if is_active := redirection["has_signed"]:
        disable_link = reverse("my-organization:redirection-disable", args=[redirection["id"]])

    return {
        "title": _("Disable redirection"),
        "active": is_active,
        "help_text": _("Disabling the redirection will prevent it from being added to the ANAF archive."),
        "action": {
            "form": disable_link,
            "name": "disable_redirection",
            "value": "true",
        },
    }


@register.filter
def redirection_dropdown(redirection: dict) -> list[dict[str, Any]]:
    return [
        _build_download_button(redirection),
        _build_disable_button(redirection),
    ]


@register.filter
def button_disabled(redirection: dict) -> bool:
    return not redirection["has_signed"]


@register.filter
def button_title(redirection: dict) -> str:
    if redirection["has_signed"]:
        return _("Form options")

    return _("All operations (i.e., downloading, disabling) are deactivated for unsigned redirections")
