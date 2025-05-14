import pytest
from django.test import RequestFactory
from django.urls import reverse

from donations.views.redirections import RedirectionHandler


class CustomRequestFactory(RequestFactory):
    def generic(
        self,
        method,
        path,
        data="",
        content_type="application/octet-stream",
        secure=False,
        *,
        headers=None,
        **extra,
    ):
        """Add a null partner to the request object"""

        request = super().generic(method, path, data, content_type, secure=secure, headers=headers, **extra)
        request.partner = None
        return request


@pytest.mark.django_db
def test_form_signature(cause):
    payload = {}
    request_factory = CustomRequestFactory()
    request = request_factory.post(reverse("twopercent", args=[cause.slug]), payload)
    response = RedirectionHandler.as_view()(request, cause_slug=cause.slug)
    print(response)
