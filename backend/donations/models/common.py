from django.db import models
from django.utils.translation import gettext_lazy as _


class CommonFilenameCacheModel(models.Model):
    """
    A model that has a cache for filenames.
    """

    filename_cache = models.JSONField(_("Filename cache"), editable=False, default=dict, blank=False, null=False)

    class Meta:
        abstract = True
