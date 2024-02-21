import logging
import mimetypes
import tempfile

import requests
from django.core.files import File
from django.db.models import Q

from donations.models.main import Ngo

logger = logging.getLogger(__name__)


def import_logos(batch_size=50):
    """
    Download and re-upload the logo files batch by batch
    """
    target_ngos = (
        Ngo.objects.exclude(Q(logo_url__isnull=True) | Q(logo_url="")).filter(Q(logo="") | Q(logo__isnull=True)).all()
    )

    if target_ngos.count() == 0:
        logger.info("No logos to import")
        return

    for ngo in target_ngos[:batch_size]:
        logger.debug("Processing logo for %s", ngo.name)

        if not ngo.logo_url.startswith("http"):
            logger.debug("Skipped logo for %s: Logo URL does not start with http", ngo.name)
            continue

        r = requests.get(ngo.logo_url)
        if r.status_code != 200:
            logger.debug("Logo file request status = %s", r.status_code)

        ext = mimetypes.guess_extension(r.headers["content-type"])
        with tempfile.TemporaryFile() as fp:
            fp.write(r.content)
            fp.seek(0)
            ngo.logo.save(f"logo{ext}", File(fp))
            logger.debug("New logo file: %s", ngo.logo)
