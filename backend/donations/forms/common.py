from django.conf import settings
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible


class ReCaptchaForm:
    fields = None

    def init_captcha(self):
        if settings.RECAPTCHA_ENABLED:
            self.fields["g-recaptcha-response"] = ReCaptchaField(widget=ReCaptchaV2Invisible)
