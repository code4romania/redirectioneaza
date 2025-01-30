from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from localflavor.generic.forms import IBANFormField
from localflavor.ro.forms import ROCIFField


class NgoPresentationForm(forms.Form):
    is_accepting_forms = forms.BooleanField(label=_("Is accepting forms"), required=False)

    name = forms.CharField(label=_("Name"), max_length=255, required=True)
    cif = ROCIFField(label=_("CUI/CIF"), required=True)
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

        super().__init__(*args, **kwargs)

        if not is_fully_editable:
            self.fields["name"].widget.attrs["disabled"] = True
            self.fields["cif"].widget.attrs["disabled"] = True
            self.fields["logo"].widget.attrs["disabled"] = True
            self.fields["website"].widget.attrs["disabled"] = True
            self.fields["contact_email"].widget.attrs["disabled"] = True
            self.fields["contact_phone"].widget.attrs["disabled"] = True
            self.fields["address"].widget.attrs["disabled"] = True
            self.fields["locality"].widget.attrs["disabled"] = True
            self.fields["county"].widget.attrs["disabled"] = True
            self.fields["active_region"].widget.attrs["disabled"] = True


class NgoFormForm(forms.Form):
    slug = forms.SlugField(label=_("Slug"), max_length=50, required=True)
    description = forms.CharField(label=_("Description"), widget=forms.Textarea, required=True)
    iban = IBANFormField(label=_("IBAN"), include_countries=("RO",), required=True)
