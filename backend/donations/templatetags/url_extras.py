from django import template
from django.conf import settings
from django.urls import reverse

register = template.Library()


@register.simple_tag
def apex_reverse(name: str):
    """
    Returns the URL with the Apex Domain included, like "//example.com/url-for-name/"
    """
    reversed = reverse(name)
    return f"//{settings.APEX_DOMAIN}{reversed}"
