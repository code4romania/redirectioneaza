from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from localflavor.generic.forms import IBANFormField
from localflavor.ro.forms import ROCIFField

from donations.common.validation.phone_number import validate_phone_number
from donations.models.ngos import Ngo


class NgoPresentationForm(forms.Form):
    is_accepting_forms = forms.BooleanField(label=_("Is accepting forms"), required=False)

    name = forms.CharField(label=_("Name"), max_length=255, required=True)
    if settings.ENABLE_FULL_CUI_VALIDATION:
        cif = ROCIFField(label=_("CUI/CIF"), required=True)
    else:
        cif = forms.CharField(label=_("CUI/CIF"), max_length=10, min_length=2, required=True)

    logo = forms.ImageField(label=_("Logo"), required=False)
    website = forms.URLField(label=_("Website"), required=False)

    contact_email = forms.EmailField(label=_("Contact email"), required=True)
    display_email = forms.BooleanField(label=_("Display email"), required=False)

    contact_phone = forms.CharField(label=_("Contact phone"), max_length=20, required=False)
    display_phone = forms.BooleanField(label=_("Display phone"), required=False)

    address = forms.CharField(label=_("Address"), max_length=255, required=True)
    locality = forms.CharField(label=_("Locality"), max_length=255, required=False)
    county = forms.ChoiceField(label=_("County"), choices=settings.FORM_COUNTIES_CHOICES, required=True)
    active_region = forms.ChoiceField(label=_("Active region"), choices=settings.FORM_COUNTIES_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        is_fully_editable = kwargs.pop("is_fully_editable", True)
        self.ngo = kwargs.pop("ngo")

        super().__init__(*args, **kwargs)

        if not is_fully_editable:
            ngohub_fields = [
                "name",
                "cif",
                "logo",
                "website",
                "contact_email",
                "contact_phone",
                "address",
                "locality",
                "county",
                "active_region",
            ]
            for field_name in ngohub_fields:
                self.fields[field_name].required = False

    def clean_cif(self):
        cif = self.cleaned_data.get("cif")

        if Ngo.objects.filter(registration_number=cif).exclude(pk=self.ngo.pk).exists():
            raise forms.ValidationError(_("An NGO with this CUI/CIF already exists."))

        return cif

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if not logo:
            return None

        # allowed types: PNG, JPG, GIF, HEIF
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/heif"]
        if logo.content_type not in allowed_types:
            raise forms.ValidationError(_("The logo type is not supported."))

        if logo.size > 2 * settings.MEBIBYTE:
            raise forms.ValidationError(_("The logo size is too large."))

        return logo

    def clean_contact_phone(self):
        raw_phone_number = self.cleaned_data["contact_phone"]

        if not raw_phone_number:
            return raw_phone_number

        phone_number_validation = validate_phone_number(raw_phone_number)

        if phone_number_validation["status"] == "error":
            raise forms.ValidationError(phone_number_validation["result"])

        return phone_number_validation["result"]


class NgoFormForm(forms.Form):
    slug = forms.SlugField(label=_("Slug"), max_length=50, required=True)
    description = forms.CharField(label=_("Description"), widget=forms.Textarea, required=True)
    iban = IBANFormField(label=_("IBAN"), include_countries=("RO",), required=True)
