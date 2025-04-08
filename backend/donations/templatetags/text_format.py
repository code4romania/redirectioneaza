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


@register.filter
def iban(value: str) -> str:
    """
    Format IBAN number to human-readable format
    AAAABBBBCCCCDDDDEEEEFFFF -> AAAA BBBB CCCC DDDD EEEE FFFF
    """

    return " ".join([value[i : i + 4] for i in range(0, len(value), 4)])
