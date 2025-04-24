from base64 import urlsafe_b64encode
from copy import deepcopy
from datetime import datetime

from cryptography.fernet import Fernet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from localflavor.ro.ro_counties import COUNTIES_CHOICES

from ..common.clean import normalize_text_alnum
from .base import DEBUG
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
FORMS_DOWNLOAD_METHOD = env.str("FORMS_DOWNLOAD_METHOD")
DONATIONS_CSV_DOWNLOAD_METHOD = env.str("DONATIONS_CSV_DOWNLOAD_METHOD")

DONATIONS_CSV_LIMIT_PER_FILE = env.int("DONATIONS_CSV_LIMIT_PER_FILE")

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
    # Colors from the Figma specifications
    # #3857B9
    {"r": 56, "g": 87, "b": 185},
    # #38B9A2
    {"r": 56, "g": 185, "b": 162},
    # #AF38B9
    {"r": 175, "g": 56, "b": 185},
    # #88B938
    {"r": 136, "g": 185, "b": 56},
    # Randomly generated colors
    {"r": 255, "g": 99, "b": 132},
    {"r": 54, "g": 162, "b": 235},
    {"r": 255, "g": 206, "b": 86},
    {"r": 75, "g": 192, "b": 192},
    {"r": 153, "g": 102, "b": 255},
    {"r": 255, "g": 159, "b": 64},
    {"r": 205, "g": 92, "b": 92},
    {"r": 50, "g": 205, "b": 50},
    {"r": 255, "g": 99, "b": 71},
    {"r": 255, "g": 215, "b": 0},
    {"r": 0, "g": 128, "b": 128},
    {"r": 0, "g": 0, "b": 128},
    {"r": 128, "g": 0, "b": 128},
    {"r": 128, "g": 0, "b": 0},
    {"r": 0, "g": 128, "b": 0},
    {"r": 0, "g": 0, "b": 0},
]

LIST_OF_COUNTIES = [county[1] for county in COUNTIES_CHOICES]

FORM_COUNTIES = deepcopy(LIST_OF_COUNTIES)
FORM_COUNTIES_CHOICES = [(county, county) for county in FORM_COUNTIES]

FORM_COUNTIES_NATIONAL = deepcopy(LIST_OF_COUNTIES)
FORM_COUNTIES_NATIONAL.insert(0, "Național")

FORM_COUNTIES_NATIONAL_CHOICES = [(county, county) for county in FORM_COUNTIES_NATIONAL]

BUCHAREST_SECTORS = ["Sector 1", "Sector 2", "Sector 3", "Sector 4", "Sector 5", "Sector 6"]
SECTORS_ITEM = {
    "title": "București",
    "values": BUCHAREST_SECTORS,
}

FORM_COUNTIES_WITHOUT_BUCHAREST = deepcopy(LIST_OF_COUNTIES)
if "București" in FORM_COUNTIES_WITHOUT_BUCHAREST:
    FORM_COUNTIES_WITHOUT_BUCHAREST.remove("București")

COUNTIES_WITH_SECTORS_LIST = BUCHAREST_SECTORS + FORM_COUNTIES_WITHOUT_BUCHAREST
FORM_COUNTIES_WITH_SECTORS_LIST = COUNTIES_WITH_SECTORS_LIST
FORM_COUNTIES_WITH_SECTORS_CHOICES = [(county, county) for county in COUNTIES_WITH_SECTORS_LIST]

FORM_COUNTIES_WITH_SECTORS = [SECTORS_ITEM] + FORM_COUNTIES_WITHOUT_BUCHAREST

COUNTIES_CHOICES_REVERSED = {name: code for code, name in COUNTIES_CHOICES}

COUNTIES_CHOICES_WITH_SECTORS = (
    tuple([(sector[0] + sector[-1], sector) for sector in BUCHAREST_SECTORS]) + COUNTIES_CHOICES
)
COUNTIES_CHOICES_WITH_SECTORS_REVERSED = {name: code for code, name in COUNTIES_CHOICES_WITH_SECTORS}
COUNTIES_CHOICES_WITH_SECTORS_REVERSED_CLEAN = {
    normalize_text_alnum(name): code for code, name in COUNTIES_CHOICES_WITH_SECTORS
}

# Encryption settings
ENCRYPT_KEY = env.str("ENCRYPT_KEY", "%INVALID%")
if len(ENCRYPT_KEY) != 32 or ENCRYPT_KEY == "%INVALID%":
    raise Exception("ENCRYPT_KEY must be exactly 32 characters long")
FERNET_OBJECT = Fernet(urlsafe_b64encode(ENCRYPT_KEY.encode("utf-8")))

FORCE_PARTNER = False
if DEBUG:
    FORCE_PARTNER = env.bool("FORCE_PARTNER", False)

SEARCH_QUERY_MIN_LENGTH = env.int("SEARCH_QUERY_MIN_LENGTH", 3)
