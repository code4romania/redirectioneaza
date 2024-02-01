from django import forms
from django.utils.translation import gettext_lazy as _
from localflavor.ro.forms import ROCNPField

from donations.models.main import Donor


class DonorInputForm(forms.ModelForm):
    street = forms.CharField(max_length=100, label=_("Strada"))
    street_number = forms.CharField(max_length=10, label=_("Număr"))
    block = forms.CharField(max_length=10, label=_("Bloc"), required=False)
    entrance = forms.CharField(max_length=10, label=_("Scara"), required=False)
    floor = forms.CharField(max_length=10, label=_("Etaj"), required=False)
    apartment = forms.CharField(max_length=10, label=_("Apartament"), required=False)
    terms = forms.BooleanField(label=_("Terms"), required=True)

    ngo_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    cnp = ROCNPField(label="CNP")

    class Meta:
        model = Donor
        fields = [
            "first_name",
            "last_name",
            "initial",
            "city",
            "county",
            "phone",
            "email",
            "is_anonymous",
            "two_years",
        ]

    @staticmethod
    def _clean_checkbox(value):
        if value == "on":
            return True
        return False

    def clean_is_anonymous(self):
        return self._clean_checkbox(self.cleaned_data["is_anonymous"])

    def clean_two_years(self):
        return self._clean_checkbox(self.cleaned_data["two_years"])

    def clean_terms(self):
        return self._clean_checkbox(self.cleaned_data["terms"])
