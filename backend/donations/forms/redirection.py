from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from localflavor.ro.forms import ROCNPField

from donations.common.validation.phone_number import validate_phone_number
from donations.forms.common import ReCaptchaMixin


class DonationForm(forms.Form, ReCaptchaMixin):
    l_name = forms.CharField(max_length=100, label=_("Last name"), required=True, strip=True)
    f_name = forms.CharField(max_length=100, label=_("First name"), required=True, strip=True)
    initial = forms.CharField(max_length=1, label=_("Initial"), required=True)

    if settings.ENABLE_FULL_VALIDATION_CNP:
        cnp = ROCNPField(label="CNP", required=True)
    else:
        cnp = forms.CharField(label="CNP", min_length=13, max_length=13, required=True)

    # limit the email address to 200 characters because that is the limit in ANAF's form
    email_address = forms.EmailField(label=_("Email"), max_length=200, required=True)
    phone_number = forms.CharField(max_length=20, label=_("Phone"), required=False, strip=True)

    street_name = forms.CharField(max_length=100, label=_("Street"), required=True, strip=True)
    street_number = forms.CharField(max_length=10, label=_("Number"), required=True, strip=True)
    flat = forms.CharField(max_length=10, label=_("Building"), required=False, strip=True)
    entrance = forms.CharField(max_length=10, label=_("Entrance"), required=False, strip=True)
    floor = forms.CharField(max_length=10, label=_("Floor"), required=False, strip=True)
    apartment = forms.CharField(max_length=10, label=_("Apartment"), required=False, strip=True)

    county = forms.CharField(max_length=100, label=_("County"), required=True)
    locality = forms.CharField(max_length=100, label=_("Locality"), required=True, strip=True)

    two_years = forms.BooleanField(label=_("Two years"), required=False)
    anaf_gdpr = forms.BooleanField(label=_("ANAF GDPR"), required=False)
    agree_contact = forms.BooleanField(label=_("Agree contact"), required=False)
    agree_terms = forms.BooleanField(label=_("Agree terms"), required=True)

    signature = forms.CharField(label=_("Signature"), max_length=1_000_000, required=False)

    def __init__(self, *args, **kwargs):
        self.recaptcha_widget = ReCaptchaV2Checkbox
        super().__init__(*args, **kwargs)

    def clean_agree_contact(self):
        return not self.cleaned_data["agree_contact"]

    def clean_signature(self):
        signature = self.cleaned_data["signature"]
        if signature and not signature.lower().startswith("data:image/svg+xml;base64,"):
            raise forms.ValidationError(_("Invalid signature format"))
        return signature

    def clean_phone_number(self):
        raw_phone_number = self.cleaned_data["phone_number"]

        if not raw_phone_number:
            return raw_phone_number

        phone_number_validation = validate_phone_number(raw_phone_number)

        if phone_number_validation["status"] == "error":
            raise forms.ValidationError(phone_number_validation["result"])

        return phone_number_validation["result"]
