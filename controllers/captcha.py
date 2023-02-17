import urllib2, urllib

from webapp2_extras import json

from appengine_config import *


VERIFY_URL = CAPTCHA_VERIFY_URL


class RecaptchaResponse(object):
    def __init__(self, is_valid, error_code=None):
        self.is_valid = is_valid
        self.error_code = error_code


def submit(recaptcha_response_field, private_key, remoteip):
    """
    Submits a reCAPTCHA request for verification. Returns RecaptchaResponse
    for the request

    recaptcha_response_field -- The value of recaptcha_response_field from the form
    private_key -- your reCAPTCHA private key
    remoteip -- the user's ip address
    """

    if not ( recaptcha_response_field and len(recaptcha_response_field) ):
        return RecaptchaResponse(is_valid = False, error_code = 'incorrect-captcha-sol')
    

    def encode_if_necessary(s):
        if isinstance(s, unicode):
            return s.encode('utf-8')
        return s

    params = urllib.urlencode({
            'secret': encode_if_necessary(private_key),
            'remoteip':  encode_if_necessary(remoteip),
            'response':  encode_if_necessary(recaptcha_response_field),
            })

    request = urllib2.Request(
        url = VERIFY_URL,
        data = params,
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "User-agent": "reCAPTCHA Python"
        }
    )
    
    try:
        httpresp = urllib2.urlopen(request)
        response = json.decode( httpresp.read() )
        httpresp.close()
    except Exception as e:
        return RecaptchaResponse(is_valid=False)

    if response["success"]:
        return RecaptchaResponse(is_valid=True)
    else:
        response_object =  RecaptchaResponse(is_valid=False)
        if "error-codes" in response:
            response_object.error_code = response["error-codes"]
        return response_object
