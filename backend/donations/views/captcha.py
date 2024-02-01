from urllib.error import HTTPError

from django.conf import settings
from django_recaptcha import client as captcha


def validate_captcha(request):
    """
    Validates the captcha
    """
    if request.method != "POST":
        return False

    captcha_response = request.POST.get("g-recaptcha-response")
    if not captcha_response:
        return False

    try:
        check_captcha = captcha.submit(captcha_response, settings.RECAPTCHA_PRIVATE_KEY, {})
    except HTTPError:
        return False

    if not check_captcha.is_valid:
        return False

    return True
