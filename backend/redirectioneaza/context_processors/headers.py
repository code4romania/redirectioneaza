from typing import Dict, List

from django.http import HttpRequest
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

HEADER_ITEMS: Dict[str, Dict[str, str]] = {
    "about": {
        "title": _("About"),
        "url": reverse_lazy("about"),
    },
    "discover_organizations": {
        "title": _("Discover organizations"),
        "url": reverse_lazy("organizations"),
        "static_icon": "search",
        "subtitle": _(
            "Still undecided about the cause you want to support? Discover the "
            "organizations you can redirect to through the platform."
        ),
    },
    "how_it_works": {
        "title": _("How it works"),
        # "url": reverse_lazy("how-it-works"),
        "static_icon": "star",
        "subtitle": _("What is the 230 form? Who can redirect? How can you contribute? What are the rules?"),
    },
    "faq_ngo": {
        "title": _("Frequently asked questions"),
        "url": reverse_lazy("faq"),
        "static_icon": "question-mark-circle",
        "subtitle": _(
            "How can you create an account for your organization? "
            "Issues using the platform? "
            "Find the answers to your questions."
        ),
    },
    "faq_user": {
        "title": _("Frequently asked questions"),
        "url": reverse_lazy("faq"),
        "static_icon": "question-mark-circle",
        "subtitle": _("What happens with your data? What else? Find the answers to your questions."),
    },
    "contact": {
        "title": _("Contact"),
        # "url": reverse_lazy("contact"),
        "static_icon": "mail",
        "subtitle": _("The contact form for donors."),
    },
    "user_guide": {
        "title": _("User guide"),
        # "url": reverse_lazy("user-guide"),
        "static_icon": "star",
        "subtitle": _(
            "Find out how you can use redirectioneaza.ro to collect the 230 forms for "
            "your organization and discover the features."
        ),
    },
    "admin_dashboard": {
        "title": _("Admin Dashboard"),
        "url": reverse_lazy("admin:index"),
        "icon": "M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z",
    },
    "admin_ngos": {
        "title": _("NGOs"),
        "url": reverse_lazy("admin:donations_ngo_changelist"),
        "icon": "M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z",
    },
    "admin_donations": {
        "title": _("Donations"),
        "url": reverse_lazy("admin:donations_donor_changelist"),
        "icon": "M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z",
    },
    "admin_partners": {
        "title": _("Partners"),
        "url": reverse_lazy("admin:partners_partner_changelist"),
        "icon": "M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z",
    },
    "admin_faq_questions": {
        "title": _("FAQ Questions"),
        "url": reverse_lazy("admin:frequent_questions_question_changelist"),
        "icon": "M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z",
    },
    "admin_users": {
        "title": _("Users"),
        "url": reverse_lazy("admin:users_user_changelist"),
        "icon": "M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z",
    },
    "ngo_dashboard": {
        "title": _("Dashboard"),
        # "url": reverse_lazy("my-organization:dashboard"),
        "icon": "M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5",
    },
    "ngo_data": {
        "title": _("Organization Data"),
        "target": "org-data",
        "url": reverse_lazy("my-organization:presentation"),
        "icon": "M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z",
    },
    "ngo_redirections": {
        "title": _("Redirections"),
        "target": "org-redirections",
        "url": reverse_lazy("my-organization:redirections"),
        "icon": "M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 0 1 9 9v.375M10.125 2.25A3.375 3.375 0 0 1 13.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 0 1 3.375 3.375M9 15l2.25 2.25L15 12",
    },
    "ngo_archives": {
        "title": _("Archive History"),
        "target": "org-archives",
        "url": reverse_lazy("my-organization:archives"),
        "icon": "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3",
    },
    "ngo_settings": {
        "title": _("Settings"),
        "target": "org-settings",
        "url": reverse_lazy("my-organization:settings"),
        "icon": "M4.5 12a7.5 7.5 0 0 0 15 0m-15 0a7.5 7.5 0 1 1 15 0m-15 0H3m16.5 0H21m-1.5 0H12m-8.457 3.077 1.41-.513m14.095-5.13 1.41-.513M5.106 17.785l1.15-.964m11.49-9.642 1.149-.964M7.501 19.795l.75-1.3m7.5-12.99.75-1.3m-6.063 16.658.26-1.477m2.605-14.772.26-1.477m0 17.726-.26-1.477M10.698 4.614l-.26-1.477M16.5 19.794l-.75-1.299M7.5 4.205 12 12m6.894 5.785-1.149-.964M6.256 7.178l-1.15-.964m15.352 8.864-1.41-.513M4.954 9.435l-1.41-.514M12.002 12l-3.75 6.495",
    },
    "log_in": {
        "title": _("Log in"),
        "url": reverse_lazy("login"),
        "style": "auth-normal",
    },
    "sign_up": {
        "title": _("Register Organization"),
        "url": reverse_lazy("signup"),
        "style": "auth-highlight",
    },
    "log_out": {
        "title": _("Log out"),
        "url": reverse_lazy("logout"),
        "style": "auth-normal",
        "icon": "M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9",
    },
    "separator": {"separator": True},
}


def build_main_menu(request: HttpRequest) -> List[Dict[str, str]]:
    if request.partner:
        return [
            HEADER_ITEMS["about"],
            HEADER_ITEMS["faq_user"],
        ]

    return [
        HEADER_ITEMS["about"],
        {
            "title": _("For donors"),
            "subtitle": (
                "Ești salariat în România? "
                "Află cum poți redirecționa 3,5% din impozitul datorat statului "
                "către o cauză în care crezi prin formularul 230, "
                "fără să te coste nimic."
            ),
            "content": [
                HEADER_ITEMS["discover_organizations"],
                # HEADER_ITEMS["how_it_works"],
                HEADER_ITEMS["faq_user"],
                # HEADER_ITEMS["contact"],
            ],
        },
        {
            "title": _("For organizations"),
            "subtitle": (
                "Faci parte dintr-o organizație non-profit? "
                "Află cum poți colecta formularele 230 folosind platforma noastră "
                "și ce presupune acest proces."
            ),
            "content": [
                # HEADER_ITEMS["how_it_works"],
                # HEADER_ITEMS["user_guide"],
                HEADER_ITEMS["faq_ngo"],
                # HEADER_ITEMS["contact"],
            ],
            "call_to_action": {
                "title": _("Register Organization"),
                "url": reverse_lazy("signup"),
            },
        },
    ]


def build_auth_menu(request: HttpRequest) -> List[Dict[str, str]]:
    user = request.user

    if not user.is_anonymous and user.is_admin:
        return [
            {
                "title": _("Admin"),
                "style": "auth-highlight",
                "content_size": "small",
                "content": [
                    HEADER_ITEMS["admin_dashboard"],
                    HEADER_ITEMS["admin_ngos"],
                    HEADER_ITEMS["admin_donations"],
                    HEADER_ITEMS["admin_partners"],
                    HEADER_ITEMS["admin_faq_questions"],
                    HEADER_ITEMS["admin_users"],
                    HEADER_ITEMS["separator"],
                    HEADER_ITEMS["log_out"],
                ],
            }
        ]

    if request.partner:
        return []

    if user.is_anonymous:
        return [
            HEADER_ITEMS["log_in"],
            HEADER_ITEMS["sign_up"],
        ]

    return [
        {
            "title": _("My Organization"),
            "style": "auth-highlight",
            "content_size": "small",
            "content": [
                # HEADER_ITEMS["ngo_dashboard"],
                HEADER_ITEMS["ngo_data"],
                HEADER_ITEMS["ngo_redirections"],
                HEADER_ITEMS["ngo_archives"],
                HEADER_ITEMS["separator"],
                HEADER_ITEMS["ngo_settings"],
                HEADER_ITEMS["separator"],
                HEADER_ITEMS["log_out"],
            ],
        }
    ]


def main(request: HttpRequest) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """
    Context processor for the header content.
    :param request: HttpRequest
    :return:
        A dictionary containing the header_content and the items for the admin, main, and auth menus.
        Nothing is returned if we're on a partner page — the header is hidden.

        Overall structure of the return dictionary:
            {
                "header_content": {
                    "main_menu": [{...}, {...}, ...],
                    "auth_menu": [{...}, {...}, ...],
                }
            }

        Each menu item is a dictionary with the following structure:
            {
                "title": <title-of-the-page>,
                "url": <url-to-the-page>,
                "static_icon": [icon-for-the-page],
                "target": [target-id-for-the-page],
                "style": ["auth-highlight", "auth-normal"],
            }
    """

    return {
        "header_content": {
            "main_menu": build_main_menu(request),
            "auth_menu": build_auth_menu(request),
        }
    }
