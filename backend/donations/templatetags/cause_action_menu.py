from typing import Any

from django import template
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from donations.models.ngos import Cause, CauseVisibilityChoices

register = template.Library()


@register.filter
def dropdown(cause: Cause) -> list[dict[str, Any]]:
    edit_cause_link = ""
    download_form_link = ""
    if can_receive_forms := cause.can_receive_redirections:
        edit_cause_link = reverse("my-organization:cause", kwargs={"cause_id": cause.pk})
        download_form_link = reverse("api-cause-form", kwargs={"cause_slug": cause.slug})

    return [
        {
            "title": _("Edit cause"),
            "active": can_receive_forms,
            "link": edit_cause_link,
        },
        {
            "title": _("Download prefilled form"),
            "active": can_receive_forms,
            "link": download_form_link,
        },
        {
            "title": _("Change to public"),
            "active": can_receive_forms and cause.visibility != CauseVisibilityChoices.PUBLIC,
            "action": {
                "form": reverse_lazy("api-change-cause-visibility"),
                "name": "visibility",
                "value": CauseVisibilityChoices.PUBLIC,
                "extra_inputs": [
                    {
                        "name": "cause_slug",
                        "value": cause.slug,
                    }
                ],
            },
        },
        {
            "title": _("Change to unlisted"),
            "active": can_receive_forms and cause.visibility != CauseVisibilityChoices.UNLISTED,
            "action": {
                "form": reverse_lazy("api-change-cause-visibility"),
                "name": "visibility",
                "value": CauseVisibilityChoices.UNLISTED,
                "extra_inputs": [
                    {
                        "name": "cause_slug",
                        "value": cause.slug,
                    }
                ],
            },
        },
        {
            "title": _("Change to private"),
            "active": can_receive_forms and cause.visibility != CauseVisibilityChoices.PRIVATE,
            "action": {
                "form": reverse_lazy("api-change-cause-visibility"),
                "name": "visibility",
                "value": CauseVisibilityChoices.PRIVATE,
                "extra_inputs": [
                    {
                        "name": "cause_slug",
                        "value": cause.slug,
                    }
                ],
            },
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
