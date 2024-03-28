
from django.http import HttpRequest
from django.templatetags.static import static


def default_ngo_logo(request: HttpRequest):
    return {"default_ngo_logo": static("images/logo_gray.png")}
