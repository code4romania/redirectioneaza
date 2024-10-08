from base64 import urlsafe_b64encode
from copy import deepcopy
from datetime import datetime

from cryptography.fernet import Fernet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from localflavor.ro.ro_counties import COUNTIES_CHOICES

from .environment import env

# Global parameters
TITLE = env.str("SITE_TITLE")

if env.bool("DONATIONS_LIMIT_TO_CURRENT_YEAR"):
    DONATIONS_LIMIT_YEAR = timezone.now().year
else:
    DONATIONS_LIMIT_YEAR = env.int("DONATIONS_LIMIT_YEAR")
DONATIONS_LIMIT_MONTH = env.int("DONATIONS_LIMIT_MONTH")
DONATIONS_LIMIT_DAY = env.int("DONATIONS_LIMIT_DAY")

DONATIONS_LIMIT = datetime(
    year=DONATIONS_LIMIT_YEAR,
    month=DONATIONS_LIMIT_MONTH,
    day=DONATIONS_LIMIT_DAY,
).date()

TIMEDELTA_DONATIONS_LIMIT_DOWNLOAD_DAYS = env.int("TIMEDELTA_DONATIONS_LIMIT_DOWNLOAD_DAYS")

DONATIONS_XML_LIMIT_PER_FILE = env.int("DONATIONS_XML_LIMIT_PER_FILE")

MONTHS = [
    {
        "month": _("January"),
        "label": _("Jan"),
    },
    {
        "month": _("February"),
        "label": _("Feb"),
    },
    {
        "month": _("March"),
        "label": _("Mar"),
    },
    {
        "month": _("April"),
        "label": _("Apr"),
    },
    {
        "month": _("May"),
        "label": _("May"),
    },
    {
        "month": _("June"),
        "label": _("Jun"),
    },
    {
        "month": _("July"),
        "label": _("Jul"),
    },
    {
        "month": _("August"),
        "label": _("Aug"),
    },
    {
        "month": _("September"),
        "label": _("Sep"),
    },
    {
        "month": _("October"),
        "label": _("Oct"),
    },
    {
        "month": _("November"),
        "label": _("Nov"),
    },
    {
        "month": _("December"),
        "label": _("Dec"),
    },
]
DONATIONS_LIMIT_MONTH_NAME = MONTHS[DONATIONS_LIMIT.month - 1]["month"]

START_YEAR = 2016

CHART_COLORS = [
    {"r": 255, "g": 99, "b": 132, "a": 0.6},
    {"r": 54, "g": 162, "b": 235, "a": 0.6},
    {"r": 255, "g": 206, "b": 86, "a": 0.6},
    {"r": 75, "g": 192, "b": 192, "a": 0.6},
    {"r": 153, "g": 102, "b": 255, "a": 0.6},
    {"r": 255, "g": 159, "b": 64, "a": 0.6},
    {"r": 205, "g": 92, "b": 92, "a": 0.6},
    {"r": 50, "g": 205, "b": 50, "a": 0.6},
    {"r": 255, "g": 99, "b": 71, "a": 0.6},
    {"r": 255, "g": 215, "b": 0, "a": 0.6},
    {"r": 0, "g": 128, "b": 128, "a": 0.6},
    {"r": 0, "g": 0, "b": 128, "a": 0.6},
    {"r": 128, "g": 0, "b": 128, "a": 0.6},
    {"r": 128, "g": 0, "b": 0, "a": 0.6},
    {"r": 0, "g": 128, "b": 0, "a": 0.6},
    {"r": 0, "g": 0, "b": 0, "a": 0.6},
]

LIST_OF_COUNTIES = [county[1] for county in COUNTIES_CHOICES]

FORM_COUNTIES = deepcopy(LIST_OF_COUNTIES)
try:
    FORM_COUNTIES.pop(LIST_OF_COUNTIES.index("București"))
except IndexError:
    pass

FORM_COUNTIES_NATIONAL = deepcopy(FORM_COUNTIES)
FORM_COUNTIES_NATIONAL.insert(0, "Național")


# Encryption settings
ENCRYPT_KEY = env.str("ENCRYPT_KEY", "%INVALID%")
if len(ENCRYPT_KEY) != 32 or ENCRYPT_KEY == "%INVALID%":
    raise Exception("ENCRYPT_KEY must be exactly 32 characters long")
FERNET_OBJECT = Fernet(urlsafe_b64encode(ENCRYPT_KEY.encode("utf-8")))
