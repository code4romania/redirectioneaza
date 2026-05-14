from django.http import HttpRequest


def custom_subdomain(request: HttpRequest):
    try:
        custom_subdomain = request.partner.subdomain if request.partner else ""
    except AttributeError:
        custom_subdomain = ""

    return {
        "custom_subdomain": custom_subdomain,
    }
