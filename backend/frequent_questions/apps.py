from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FrequentQuestionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "frequent_questions"
    verbose_name = _("Frequent Questions")
