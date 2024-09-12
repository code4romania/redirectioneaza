from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImporterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "importer"
    verbose_name = _("Importer")
