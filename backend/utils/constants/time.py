# Constants for time
from django.utils.translation import gettext_lazy as _

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR

DAY_IN_DAYS = 1
WEEK_IN_DAYS = 7 * DAY_IN_DAYS
MONTH_IN_DAYS = 30 * DAY_IN_DAYS
YEAR_IN_DAYS = 365 * DAY_IN_DAYS


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
