from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def create_error_view(error_code: int) -> callable:
    """
    Return a callable for handling different error codes
    """

    def custom_error_view(request: HttpRequest, exception: Exception = None) -> HttpResponse:
        if error_code in (400, 403, 404, 500):
            response = render(request, f"errors/{error_code}.html")
            response.status_code = error_code
        else:
            response = render(request, "errors/other.html")
        return response

    return custom_error_view
