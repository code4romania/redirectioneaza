from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def url_validator(value):
    if value in ("redirectioneaza", "www", "admin", "api", "ftp", "dns", "ns1", "ns2"):
        raise ValidationError(_("This subdomain is reserved."))

    if not value.islower():
        raise ValidationError(_("Subdomain must contain only lowercase characters."))

    if not "".join(value.split("-")).isalnum():
        raise ValidationError(_("Subdomain must contain only alphanumeric characters and '-' (hyphens)."))

    if not (3 <= len(value) <= 100):
        raise ValidationError(_("Subdomain must have between 3 and 100 characters."))
