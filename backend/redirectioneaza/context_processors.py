from django.http import HttpRequest
from django.urls import reverse


def headers(request: HttpRequest):
    if request.partner:
        return {}

    return {
        "header_content": {
            "main_menu": [
                {
                    "title": "Despre",
                    "url": reverse("about"),
                },
                {
                    "title": "Pentru contribuabili",
                    "subtitle": (
                        "Ești salariat în România? "
                        "Află cum poți redirecționa 3,5% din impozitul datorat statului "
                        "către o cauză în care crezi prin formularul 230, "
                        "fără să te coste nimic."
                    ),
                    "content": [
                        {
                            "title": "Descoperă organizații",
                            "url": reverse("organizations"),
                            "icon": "search",
                            "subtitle": (
                                "Încă nu te-ai hotărât cu privire la cauza pe care vrei să o susții? "
                                "Descoperă organizațiile către care poți redirecționa prin platformă."
                            ),
                        },
                        # {
                        #     "title": "Cum funcționează",
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
                            "title": "Întrebări frecvente",
                            "url": reverse("faq"),
                            "icon": "question-mark-circle",
                            "subtitle": (
                                "Ce se întâmplă cu datele tale? Ce altceva? Găsește răspunsurile la întrebările tale."
                            ),
                        },
                        # {
                        #     "title": "Contact",
                        #     "url": reverse("contact"),
                        #     "icon": "mail",
                        #     "subtitle": "Pagina formular contact pentru donatori.",
                        # },
                    ],
                },
                {
                    "title": "Pentru organizații",
                    "subtitle": (
                        "Faci parte dintr-o organizație non-profit? "
                        "Află cum poți colecta formularele 230 folosind platforma noastră "
                        "și ce presupune acest proces."
                    ),
                    "content": [
                        # {
                        #     "title": "Cum funcționează",
                        #     "url": reverse("how-it-works"),
                        #     "icon": "star",
                        #     "subtitle": "Ce este formularul 230? Cum se poate colecta, și cum se poate depune?",
                        # },
                        # {
                        #     "title": "Ghidul utilizatorului redirectionează.ro",
                        #     "url": reverse("user-guide"),
                        #     "icon": "star",
                        #     "subtitle": (
                        #         "Află cum poți folosi platforma redirectionează.ro "
                        #         "pentru a strânge formularele 230 pentru organizația ta și descoperă funcționalitățile."
                        #     ),
                        # },
                        {
                            "title": "Întrebări frecvente",
                            "url": reverse("faq"),
                            "icon": "question-mark-circle",
                            "subtitle": (
                                "Cum poți crea un cont pentru organizația ta? "
                                "Probleme în utilizarea platformei? "
                                "Găsește răspunsurile la întrebările tale."
                            ),
                        },
                        # {
                        #     "title": "Contact",
                        #     "url": reverse("contact"),
                        #     "icon": "mail",
                        #     "subtitle": "Pagina formular contact pentru organizații.",
                        # },
                    ],
                    "call_to_action": {
                        "title": "Înregistrează organizația",
                        "url": reverse("signup"),
                    },
                },
            ],
            "auth_menu": [
                {
                    "title": "Intră în cont ONG",
                    "url": reverse("login"),
                },
                {
                    "title": "Înregistrează ONG",
                    "url": reverse("signup"),
                    "style": "highlight",
                },
            ],
        }
    }
