from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def to_county(value):
    try:
        sector_value = int(value)
        return _("Sector %s") % sector_value
    except ValueError:
        return value
