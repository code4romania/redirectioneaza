from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render

from .base import AccountHandler


class MyAccountDetailsHandler(AccountHandler):
    pass


@method_decorator(login_required, name="get")
class MyAccountHandler(AccountHandler):
    template_name = "ngo/my-account.html"

    def get(self, request):
        context = {
            "user": request.user,
            # TODO:
            "ngo": None,
        }
        return render(request, self.template_name, context)


class NgoDetailsHandler(AccountHandler):
    pass
