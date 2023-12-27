from django.conf import settings
from django.http import Http404

from .models import Partner


class InvalidSubdomain(Exception):
    pass


class PartnerDomainMiddleware:
    """
    Add the `request.partner` property based on the requested subdomain
    """

    @staticmethod
    def extract_subdomain(host: str, apex: str) -> str:
        apex = apex.strip().lower()
        dot_apex = "." + apex
        host = host.strip().lower()

        # Drop the port number (if present)
        host = host.split(":", maxsplit=1)[0]

        # Drop the www. prefix (if present)
        if host[:4] == "www.":
            host = host[4:]

        # Extract the subdomain name
        if host == apex:
            subdomain = ""
        elif host.endswith(dot_apex):
            subdomain = host.split(dot_apex, maxsplit=1)[0]
        else:
            raise InvalidSubdomain

        return subdomain

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            subdomain = PartnerDomainMiddleware.extract_subdomain(request.get_host(), settings.APEX_DOMAIN)
        except InvalidSubdomain:
            raise Http404

        if not subdomain:
            partner = None
        else:
            try:
                partner = Partner.objects.get(subdomain=subdomain)
            except Partner.DoesNotExist:
                partner = None

        request.partner = partner

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
