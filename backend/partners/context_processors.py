from django.http import HttpRequest


def custom_subdomain(request: HttpRequest):
    return {
        "custom_subdomain": request.partner.subdomain if request.partner else "",
    }
