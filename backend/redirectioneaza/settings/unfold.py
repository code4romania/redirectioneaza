from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .app_configs import TITLE
from .base import VERSION_LABEL

# Unfold Admin settings

SIDEBAR_NAVIGATION = [
    # Supported icon set: https://fonts.google.com/icons
    {
        "title": _("Dashboard"),
        "items": [
            {
                "title": _("Dashboard"),
                "icon": "dashboard",
                "link": reverse_lazy("admin:index"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Home page"),
                "icon": "dashboard",
                "link": reverse_lazy("admin:index"),
                "permission": lambda request: not request.user.is_superuser,
            },
        ],
    },
    {
        "title": _("Donations"),
        "items": [
            {
                "title": _("NGOs"),
                "icon": "foundation",
                "link": reverse_lazy("admin:donations_ngo_changelist"),
                "permission": lambda request: request.user.is_staff,
            },
            {
                "title": _("Causes"),
                "icon": "help_clinic",
                "link": reverse_lazy("admin:donations_cause_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Donations"),
                "icon": "edit_document",
                "link": reverse_lazy("admin:donations_donor_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Donation exports"),
                "icon": "file_copy",
                "link": reverse_lazy("admin:donations_job_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Partners"),
                "icon": "handshake",
                "link": reverse_lazy("admin:partners_partner_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },
    {
        "title": _("Frequently asked questions"),
        "items": [
            {
                "title": _("Sections"),
                "icon": "folder",
                "link": reverse_lazy("admin:frequent_questions_section_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Questions"),
                "icon": "help",
                "link": reverse_lazy("admin:frequent_questions_question_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },
    {
        "title": _("Users"),
        "items": [
            {
                "title": _("Users"),
                "icon": "person",
                "link": reverse_lazy("admin:users_user_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Groups"),
                "icon": "group",
                "link": reverse_lazy("admin:users_groupproxy_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },
    {
        "title": _("Background Tasks"),
        "items": [
            {
                "title": _("Failed tasks"),
                "icon": "assignment_late",
                "link": reverse_lazy("admin:django_q_failure_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Queued tasks"),
                "icon": "assignment_add",
                "link": reverse_lazy("admin:django_q_ormq_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Scheduled tasks"),
                "icon": "assignment",
                "link": reverse_lazy("admin:django_q_schedule_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Successful tasks"),
                "icon": "assignment_turned_in",
                "link": reverse_lazy("admin:django_q_success_changelist"),
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },
]

UNFOLD = {
    # https://unfoldadmin.com/docs/configuration/settings/
    # Site configuration
    "ENVIRONMENT": "redirectioneaza.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "donations.views.dashboard.dashboard.callback",
    # Site customization
    "SITE_HEADER": f"Admin | {VERSION_LABEL}",
    "SITE_TITLE": TITLE,
    "SITE_ICON": lambda request: static("images/logo-smaller.png"),
    "SITE_LOGO": lambda request: static("images/logo-smaller.png"),
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "16x16",
            "type": "image/png",
            "href": lambda request: static("images/favicon/favicon-16x16.png"),
        },
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": lambda request: static("images/favicon/favicon-32x32.png"),
        },
    ],
    "COLORS": {
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",
            "default-light": "75 85 99",
            "default-dark": "209 213 219",
            "important-light": "17 24 39",
            "important-dark": "243 244 246",
        },
        "primary": {
            "50": "#FEFDE8",
            "100": "#FEFBC3",
            "200": "#FEF38A",
            "300": "#FCE548",
            "400": "#F9D00B",
            "500": "#E9B909",
            "600": "#C99005",
            "700": "#A16607",
            "800": "#85500E",
            "900": "#714212",
            "950": "#422206",
        },
    },
    # Sidebar settings
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": SIDEBAR_NAVIGATION,
    },
}
