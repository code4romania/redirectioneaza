from django.conf import settings
from django.test import Client


class ApexClient(Client):
    def __init__(
        self,
        enforce_csrf_checks=False,
        raise_request_exception=True,
        *,
        headers=None,
        query_params=None,
        **defaults,
    ):
        # set a default SERVER_NAME and HTTP_HOST if no custom names are provided
        defaults["SERVER_NAME"] = defaults.get("SERVER_NAME", settings.APEX_DOMAIN.split(":")[0])
        defaults["HTTP_HOST"] = defaults.get("HTTP_HOST", settings.APEX_DOMAIN)  # Docs recommend the headers parameter

        super().__init__(headers=headers, query_params=query_params, **defaults)
