import random
from datetime import datetime

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from frequent_questions.models import Question
from partners.models import DisplayOrderingChoices
from redirectioneaza.common.cache import cache_decorator

from ..models.donors import Donor
from ..models.ngos import ALL_NGO_IDS_CACHE_KEY, ALL_NGOS_CACHE_KEY, FRONTPAGE_NGOS_KEY, Ngo


class HomePage(TemplateView):
    template_name = "index.html"

    @staticmethod
    @cache_decorator(timeout=settings.TIMEOUT_CACHE_LONG, cache_key_prefix=ALL_NGO_IDS_CACHE_KEY)
    def _get_list_of_ngo_ids() -> list:
        return list(Ngo.active.values_list("id", flat=True))

    def get(self, request, *args, **kwargs):
        now = timezone.now()

        context = {
            "title": "redirectioneaza.ro",
            "limit": settings.DONATIONS_LIMIT,
            "current_year": now.year,
        }

        if partner := request.partner:
            partner_ngos = partner.ngos.all()

            if partner.display_ordering == DisplayOrderingChoices.ALPHABETICAL:
                partner_ngos = partner_ngos.order_by("name")
            elif partner.display_ordering == DisplayOrderingChoices.NEWEST:
                partner_ngos = partner_ngos.order_by("-date_created")
            elif partner.display_ordering == DisplayOrderingChoices.RANDOM:
                random.shuffle(list(partner_ngos))

            context.update(
                {
                    "company_name": partner.name,
                    "custom_header": partner.has_custom_header,
                    "custom_note": partner.has_custom_note,
                    "ngos": partner_ngos,
                }
            )
        else:
            ngo_queryset = Ngo.active
            start_of_year = datetime(now.year, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
            context["stats"] = {
                "ngos": ngo_queryset.count(),
                "forms": Donor.objects.filter(date_created__gte=start_of_year).count(),
            }

            context["ngos"] = self._get_random_ngos(ngo_queryset, num_ngos=min(4, ngo_queryset.count()))

        return render(request, self.template_name, context)

    @cache_decorator(timeout=settings.TIMEOUT_CACHE_SHORT, cache_key_prefix=FRONTPAGE_NGOS_KEY)
    def _get_random_ngos(self, ngo_queryset: QuerySet, num_ngos: int):
        all_ngo_ids = self._get_list_of_ngo_ids()
        return ngo_queryset.filter(id__in=random.sample(all_ngo_ids, num_ngos))


class AboutHandler(TemplateView):
    template_name = "despre.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Despre Redirectioneaza.ro"}
        return render(request, self.template_name, context)


class NgoListHandler(TemplateView):
    template_name = "all-ngos.html"

    @staticmethod
    @cache_decorator(timeout=settings.TIMEOUT_CACHE_NORMAL, cache_key=ALL_NGOS_CACHE_KEY)
    def _get_all_ngos() -> list:
        return Ngo.active.order_by("name")

    def get(self, request, *args, **kwargs):
        # TODO: the search isn't working
        # TODO: add pagination
        context = {
            "title": "Toate ONG-urile",
            "ngos": self._get_all_ngos(),
        }

        return render(request, self.template_name, context)


class NoteHandler(TemplateView):
    template_name = "note.html"

    def get(self, request, *args, **kwargs):
        context = {
            "title": "Notă de informare",
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        return render(request, self.template_name, context)


class FAQHandler(TemplateView):
    template_name = "public/faq.html"

    def get_questions(self):
        # TODO: transform this into an import for the FAQ model

        donation_deadline = settings.DONATIONS_LIMIT
        contact_email = settings.CONTACT_EMAIL_ADDRESS

        return [
            {
                "title": _("For NGOs"),
                "questions": [
                    {
                        "title": _("Ce informații sunt necesare pentru a crea un cont de organizație?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Pentru a crea un profil de organizație pe platformă sunt necesare următoarele date:
                denumirea legală a organizației, adresa, regiunea în care își desfășoară activitatea,
                CUI/CIF, IBAN, o scurtă descriere și logo-ul.
                Toate aceste informații pot fi editate și ulterior, dacă este necesar.
            </p>
            <p>
                <strong>
                    Atenție!
                    Aceste informații sunt preluate automat pentru completarea Declarației 230.
                    Orice posibilă greșeală în datele organizației va determina crearea unor declarații
                    invalide.
                </strong>
            </p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("În cât timp după crearea paginii organizației aceasta devine activă?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                După crearea paginii aceasta devine imediat activă,
                ceea ce înseamnă că pot fi colectate formulare de redirecționare a impozitului pe venit.
                Verificați link-ul (URL-ul) înainte de a-l distribui mai departe,
                ca să vă asigurați că cei care vor să redirecționeze nu vor întâmpina dificultăți.
            </p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("După crearea contului, ce date asociate contului organizației pot fi editate?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Din contul organizației se pot edita toate informațiile:
                nume, descriere, adresă, regiunea în care își desfășoară activitatea, URL, CUI/CIF, IBAN.
            </p>
            <p>
                De asemenea, tot de pe aceeași pagină se pot selecta și deselecta următoarele opțiuni:
            </p>
            <ul>
                <li>
                    Asociație înregistrată ca furnizor autorizat de servicii sociale;
                </li>
                <li>
                    Doresc să primesc formularele completate pe email.
                </li>
            </ul>
                        """
                            )
                        ),
                    },
                    {
                        "title": _(
                            "Dacă editez date ale organizației care apar pe Declarația 230, acestea sunt automat modificate pe noile declarații?"
                        ),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Modificările realizate în contul organizației vor fi vizibile online în câteva minute,
                pe platforma Redirecționează și imediat în noile declarații depuse de contribuabili.
            </p>
            <p><strong>
                Atenție!
                Declarațiile deja completate de către contribuabili vor păstra informațiile vechi,
                valabile la data completării lor.
            </strong></p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("Cum se poate activa opțiunea de semnare online a formularelor?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Pentru ca organizația să poată primi formularele deja semnate de către contribuabili,
                în contul organizației trebuie bifată opțiunea:
                <strong>
                    ”Doresc să primesc formularele completate pe email.
                    Selectând aceasta opțiune confirm că ONG-ul are cont SPV pentru a depune formularele.”
                </strong>
            </p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("Cum se poate schimba adresa de e-mail asociată contului organizației?"),
                        "answer": mark_safe(
                            _(
                                f"""
            <p>
                Pentru a schimba adresa de e-mail asociată contului sunt necesari câțiva pași:
            </p>
            <ul>
                <li>
                    Creați un nou cont pe redirectioneaza.ro cu noua adresă pe care vreți să o folosiți,
                    fără a completa datele ONG-ului.
                </li>
                <li>
                    Trimiteți-ne un e-mail pe adresa
                    <a href="mailto:{contact_email}">{contact_email}</a>
                    în care să soliciți schimbarea adresei atașate contului,
                    atașând mesajului certificatul de înregistrare al organizației
                    și un document care să ateste poziția solicitantului în ONG
                    (ex:declarație semnată de conducerea organizației).
                </li>
            </ul>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("Pot crea mai multe conturi pentru aceeași organizație?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Nu pot fi create mai multe conturi pe platforma Redirecționează pentru aceeași organizație.
                Fiecărui CUI/CIF îi poate corespunde un singur cont pe redirectioneaza.ro
            </p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _(
                            "Mai este necesar să depun la ANAF declarațiile primite pe platforma Redirecționează?"
                        ),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Prin intermediul platformei Redirecționează se pot doar colecta
                declarațiile de la contribuabili.
                Este în continuare obligația fiecărei organizații neguvernamentale de a depune la ANAF
                formularul unic ce conține informațiile despre fiecare declarație de
                redirecționare a procentului de 3,5% din impozitul pe venit.
                Pentru a facilita acest proces, din contul organizației de pe platforma Redirecționează,
                poți descărca o arhivă ce conține următoarele documente:
            </p>
            <ul>
                <li>
                    Un fișier HTML (se deschide în orice browser – ex.
                    Chrome, Safari, Edge)
                    cu informații despre conținutul arhivei
                    și cu explicațiile pașilor necesari pentru a depune
                    declarațiile în conformitate cu cerințele ANAF
                </li>
                <li>
                    Un fișier CSV cu informații care centralizează datele contribuabililor
                </li>
                <li>
                    Un dosar/folder cu formularele completate de către contribuabili
                </li>
                <li>
                    Un dosar/folder cu fișierele XML ce pot fi încărcate în PDF-ul ANAF
                </li>
            </ul>
                        """
                            )
                        ),
                    },
                ],
            },
            {
                "title": _("For Donors"),
                "questions": [
                    {
                        "title": _("Cine poate redirecționa 3,5% din impozitul pe venit?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Formularul se completează și se depune de către persoanele fizice care realizează
                următoarele venituri din România:
            </p>
            <ul>
                <li>
                    Venituri din salarii și asimilate salariilor;
                </li>
                <li>
                    Venituri din pensii;
                </li>
                <li>
                    Venituri din activități independente impuse pe bază de normă de venit;
                </li>
                <li>
                    Activități agricole impuse pe bază de normă de venit;
                </li>
                <li>
                    Venituri din activități independente realizate în baza contractelor de
                    activitate sportivă, pentru care impozitul se reține la sursă;
                </li>
                <li>
                    Venituri din drepturi de proprietate intelectuală,
                    altele decât cele pentru care venitul net se determină în sistem real;
                </li>
                <li>
                    Venituri din cedarea folosinței bunurilor pentru care venitul net se determină
                    pe baza normelor de venit și venituri din cedarea folosinței bunurilor
                    pentru care venitul net se determină pe baza cotelor forfetare de cheltuieli.
                </li>
            </ul>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("Cum pot redirecționa 3,5% din impozitul pe venit?"),
                        "answer": mark_safe(
                            _(
                                f"""
            <p>
                Redirecționarea procentului din impozitul pe venit se face prin depunerea declarației 230
                până la data de {donation_deadline.strftime("%d.%m.%Y")}.
                Există trei variante de a depune declarația:
            </p>
            <ol>
                <li>
                    Poți depune declarația personal, în format fizic la registratura organului fiscal
                    de care aparții sau prin poștă la adresa serviciului fiscal.
                </li>
                <li>
                    Poți depune electronic, prin serviciul Spațiul Privat Virtual personal.
                </li>
                <li>
                    Poți trimite formularul către organizația pentru care dorești să redirecționezi
                    și ei se vor ocupa de depunerea acestora către ANAF.
                    Prin intermediul platformei Redirecționează,
                    poți face acest lucru semnând declarația
                    <a href="{reverse('organizations')}">aici</a>.
                </li>
            </ol>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("Pot depune mai multe declarații?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Nu, pe platforma redirectioneaza.ro se poate completa și
                depune declarația 230 pentru o singură organizație.
                Dacă veți depune mai multe astfel de declarații,
                veți fi contactat ulterior de către autorități pentru a verifica pe care vreți să o
                păstrați.
            </p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("După ce am semnat declarația, mă mai pot răzgândi?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Odată semnată declarația online prin intermediul platformei,
                acesta nu mai poate fi retrasă din centralizarea organizației
                către care ați ales să redirecționați cei 3,5% din impozitul pe venit.
            </p>
                        """
                            )
                        ),
                    },
                    {
                        "title": _("Dacă am semnat declarația online, mai este necesar să o depun și eu la ANAF?"),
                        "answer": mark_safe(
                            _(
                                """
            <p>
                Nu.
                Odată semnată online, declarația este transmisă automat organizației către care
                ați ales să redirecționați procentul din impozitul pe venit.
                Devine astfel responsabilitatea organizației să transmită către
                Agenția Națională de Administrare Fiscală
                situația centralizată cu toate declarațiile primite.
                Dacă vreți să vă retrageți declarația după depunere,
                trebuie să luați legătura direct cu organizația pentru care ai completat declarația.
            </p>
          </div>
                        """
                            )
                        ),
                    },
                ],
            },
        ]

    def get(self, request, *args, **kwargs):
        questions = Question.get_all()

        context = {
            "title": _("Frequently Asked Questions"),
            "questions": questions,
        }
        return render(request, self.template_name, context)


class PolicyHandler(TemplateView):
    template_name = "policy.html"

    def get(self, request, *args, **kwargs):
        context = {"title": "Politica de confidențialitate"}
        return render(request, self.template_name, context)


class TermsHandler(TemplateView):
    template_name = "terms.html"

    def get(self, request, *args, **kwargs):
        context = {
            "title": "Termeni și condiții",
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        return render(request, self.template_name, context)


class HealthCheckHandler(TemplateView):
    def get(self, request, *args, **kwargs):
        # return HttpResponse(str(request.headers))
        return HttpResponse("OK")
