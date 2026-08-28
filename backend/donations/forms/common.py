from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible


class ReCaptchaMixin:
    fields: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.recaptcha_widget = ReCaptchaV2Invisible
        self.init_captcha()

    def init_captcha(self):
        if settings.RECAPTCHA_ENABLED:
            self.fields["g-recaptcha-response"] = ReCaptchaField(widget=self.recaptcha_widget)


class TwoPasswordMixin:
    cleaned_data: dict
    password: str
    password_confirm: str

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not password:
            raise forms.ValidationError(_("Password is required"))
        return password

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")

        # The comparison is safe since we're in the registration step
        # noinspection TimingAttack
        if password != password_confirm:
            raise forms.ValidationError(_("Passwords do not match"))

        return password_confirm
