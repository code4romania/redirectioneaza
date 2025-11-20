from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField


class Section(models.Model):
    title = models.CharField(_("Title"), max_length=255)

    order = models.IntegerField(_("Order"), default=0)

    class Meta:
        ordering = ["order", "title"]

        verbose_name = _("Section")
        verbose_name_plural = _("Sections")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.order == 0:
            number_of_sections = Section.objects.all().count()
            self.order = number_of_sections + 1

        super().save(*args, **kwargs)


class Question(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="questions")

    title = models.CharField(_("Question"), max_length=255)
    answer = HTMLField(_("Answer"))

    order = models.IntegerField(_("Order"), default=0)

    class Meta:
        ordering = ["order", "title"]

        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.order == 0:
            number_of_questions = Question.objects.filter(section=self.section).count()
            self.order = number_of_questions + 1

        super().save(*args, **kwargs)

    @staticmethod
    def get_all():
        """
        Get all questions grouped by section.
        :return:
        [
            {
                "title": "section1",
                "questions": [
                    {"title": "question1", "answer": "answer1"},
                    {"title": "question2", "answer": "answer2"},
                ]
            },
        ]
        """

        sections = Section.objects.all()

        questions = []
        for section in sections:
            questions.append(
                {
                    "title": section.title,
                    "questions": [
                        {"title": question.title, "answer": question.answer}
                        for question in Question.objects.filter(section=section)
                    ],
                }
            )

        return questions


auditlog.register(Section)
auditlog.register(Question)
