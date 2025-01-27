import logging

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponse
from django.views.generic import TemplateView

from donations.models.ngos import Ngo

logger = logging.getLogger(__name__)


class NgoRemoveForms(TemplateView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied()

        total_removed = 0

        # get all the ngos
        ngos = Ngo.objects.all()

        logger.info("Removing form_url and prefilled_form from {0} ngos.".format(len(ngos)))

        # loop through them and remove the form_url
        # this will force an update on it when downloaded again
        for ngo in ngos:
            try:
                ngo.prefilled_form.delete()
                total_removed += 1
            except IntegrityError as e:
                logger.error("IntegrityError removing `form_url` from ngo {0}: {1}".format(ngo.id, e))
            except Exception as e:
                logger.error("Error removing `form_url` from ngo {0}: {1}".format(ngo.id, e))

        return HttpResponse("Removed {} form files".format(total_removed))
