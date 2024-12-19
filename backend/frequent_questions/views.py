from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from frequent_questions.models import Question


class FAQHandler(TemplateView):
    template_name = "public/faq.html"

    def get(self, request, *args, **kwargs):
        questions = Question.get_all()

        context = {
            "title": _("Frequently Asked Questions"),
            "questions": questions,
        }
        return render(request, self.template_name, context)
