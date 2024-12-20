from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext as _

from donations.views.base import BaseVisibleTemplateView
from frequent_questions.models import Question


class FAQHandler(BaseVisibleTemplateView):
    template_name = "public/faq.html"
    title = _("Frequently Asked Questions")

    def get(self, request, *args, **kwargs):
        questions = Question.get_all()

        context = {
            "title": _("Frequently Asked Questions"),
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
            "questions": questions,
        }
        return render(request, self.template_name, context)
