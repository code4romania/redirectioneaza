from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible
from localflavor.ro.forms import ROCNPField


class DonationForm(forms.Form):
    l_name = forms.CharField(max_length=100, label=_("Last name"), required=True, strip=True)
    f_name = forms.CharField(max_length=100, label=_("First name"), required=True, strip=True)
    initial = forms.CharField(max_length=1, label=_("Initial"), required=True)
    cnp = ROCNPField(label="CNP", required=True)

    email_address = forms.EmailField(label=_("Email"), required=True)
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
    agree_contact = forms.BooleanField(label=_("Agree contact"), required=True)
    agree_terms = forms.BooleanField(label=_("Agree terms"), required=True)

    signature = forms.CharField(label=_("Signature"), max_length=1_000_000, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.RECAPTCHA_ENABLED:
            self.fields["captcha_token"] = ReCaptchaField(widget=ReCaptchaV2Invisible)

    def clean_agree_contact(self):
        return not self.cleaned_data["agree_contact"]
