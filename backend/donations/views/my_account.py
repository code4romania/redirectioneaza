from django.shortcuts import render
from django.conf import settings

from .base import BaseHandler, AccountHandler


class MyAccountDetailsHandler(AccountHandler):
    pass


class MyAccountHandler(AccountHandler):
    pass


class NgoDetailsHandler(AccountHandler):
    pass
