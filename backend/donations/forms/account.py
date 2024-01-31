from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from donations.forms.common import ReCaptchaForm
from secrets import compare_digest


class LoginForm(forms.Form, ReCaptchaForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True, max_length=150)

    class Meta:
        fields = ["email", "password"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_captcha()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email:
            raise forms.ValidationError(_("Email is required"))
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not password:
            raise forms.ValidationError(_("Password is required"))
        return password


class RegisterForm(forms.ModelForm, ReCaptchaForm):
    password_confirm = forms.CharField(widget=forms.PasswordInput(), required=True, max_length=150)

    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password_confirm",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_captcha()

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"]
        if not first_name:
            raise forms.ValidationError(_("First name is required"))
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"]
        if not last_name:
            raise forms.ValidationError(_("Last name is required"))
        return last_name

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not email:
            raise forms.ValidationError(_("Email is required"))
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not password:
            raise forms.ValidationError(_("Password is required"))
        return password

    def clean_password_confirm(self):
        password = self.cleaned_data["password"]
        password_confirm = self.cleaned_data["password_confirm"]
        if not compare_digest(password, password_confirm):
            raise forms.ValidationError(_("Passwords do not match"))
        return password_confirm
