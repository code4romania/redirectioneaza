from typing import Dict, List

from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _


def headers(request: HttpRequest) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """
    Context processor for the header content.
    :param request: HttpRequest
    :return:
        A dictionary containing the header_content and the items for the admin, main, and auth menus.
        Nothing is returned if we're on a partner page — the header is hidden.

        Overall structure of the return dictionary:
            {
                "header_content": {
                    "admin_menu": [{...}, {...}, ...],
                    "main_menu": [{...}, {...}, ...],
                    "auth_menu": [{...}, {...}, ...],
                }
            }

        Each menu item is a dictionary with the following structure:
            {
                "title": <title-of-the-page>,
                "url": <url-to-the-page>,
                "icon": [icon-for-the-page],
                "target": [target-id-for-the-page],
                "style": ["auth-highlight", "auth-normal"],
            }
    """

    if request.partner:
        return {}

    admin_header_menu = []

    main_header_menu = [
        {
            "title": _("About"),
            "url": reverse("about"),
        },
        {
            "title": _("For donors"),
            "subtitle": (
                "Ești salariat în România? "
                "Află cum poți redirecționa 3,5% din impozitul datorat statului "
                "către o cauză în care crezi prin formularul 230, "
                "fără să te coste nimic."
            ),
            "content": [
                {
                    "title": _("Discover organizations"),
                    "url": reverse("organizations"),
                    "icon": "search",
                    "subtitle": (
                        "Încă nu te-ai hotărât cu privire la cauza pe care vrei să o susții? "
                        "Descoperă organizațiile către care poți redirecționa prin platformă."
                    ),
                },
                # {
                #     "title": _("How it works"),
                #     "url": reverse("how-it-works"),
                #     "icon": "star",
                #     "subtitle": (
                #         "Ce este formularul 230? "
                #         "Cine poate redirecționa? "
                #         "Cum poți contribui? "
                #         "Care sunt regulile?"
                #     ),
                # },
                {
                    "title": _("Frequently asked questions"),
                    "url": reverse("faq"),
                    "icon": "question-mark-circle",
                    "subtitle": (
                        "Ce se întâmplă cu datele tale? Ce altceva? Găsește răspunsurile la întrebările tale."
                    ),
                },
                # {
                #     "title": _("Contact"),
                #     "url": reverse("contact"),
                #     "icon": "mail",
                #     "subtitle": "Pagina formular contact pentru donatori.",
                # },
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
                # {
                #    "title": _("How it works"),
                #     "url": reverse("how-it-works"),
                #     "icon": "star",
                #     "subtitle": "Ce este formularul 230? Cum se poate colecta, și cum se poate depune?",
                # },
                # {
                #     "title": _("User guide"),
                #     "url": reverse("user-guide"),
                #     "icon": "star",
                #     "subtitle": (
                #         "Află cum poți folosi platforma redirectionează.ro "
                #         "pentru a strânge formularele 230 pentru organizația ta și descoperă funcționalitățile."
                #     ),
                # },
                {
                    "title": _("Frequently asked questions"),
                    "url": reverse("faq"),
                    "icon": "question-mark-circle",
                    "subtitle": (
                        "Cum poți crea un cont pentru organizația ta? "
                        "Probleme în utilizarea platformei? "
                        "Găsește răspunsurile la întrebările tale."
                    ),
                },
                # {
                #     "title": _("Contact"),
                #     "url": reverse("contact"),
                #     "icon": "mail",
                #     "subtitle": "Pagina formular contact pentru organizații.",
                # },
            ],
            "call_to_action": {
                "title": _("Register Organization"),
                "url": reverse("signup"),
            },
        },
    ]

    user = request.user
    if user.is_anonymous:
        auth_menu_content = [
            {
                "title": _("Log in"),
                "url": reverse("login"),
                "style": "auth-normal",
            },
            {
                "title": _("Register Organization"),
                "url": reverse("signup"),
                "style": "auth-highlight",
            },
        ]
    else:
        auth_menu_content = [
            {
                "title": _("Log out"),
                "url": reverse("logout"),
                "style": "auth-normal",
            },
            {
                "title": _("My organization"),
                "url": reverse("my-organization:presentation"),
                "style": "auth-highlight",
            },
        ]

    if user.is_authenticated and user.ngo:
        admin_header_menu = [
            # {
            #     "title": _("Dashboard"),
            #     "url": reverse("my-organization:dashboard"),
            #     "icon": "M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5"
            # },
            {
                "title": _("Organization Data"),
                "target": "organization-data",
                "url": reverse("my-organization:presentation"),
                "icon": "M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z",
            },
            {
                "title": _("Redirections"),
                "target": "org-redirections",
                "url": reverse("my-organization:redirections"),
                "icon": "M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 0 1 9 9v.375M10.125 2.25A3.375 3.375 0 0 1 13.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 0 1 3.375 3.375M9 15l2.25 2.25L15 12",
            },
            {
                "title": _("Archive History"),
                "target": "org-archives",
                "url": reverse("my-organization:archives"),
                "icon": "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3",
            },
        ]

    return {
        "header_content": {
            "admin_menu": admin_header_menu,
            "main_menu": main_header_menu,
            "auth_menu": auth_menu_content,
        }
    }
