import requests
import tempfile
import mimetypes

from django.db.models import Q
from django.core.files import File
from django.core.management import BaseCommand

from donations.models.main import Ngo


def _import_logos(batch_size=50):
    """
    Download an reupload the logo files one by one
    """
    for ngo in (
        Ngo.objects.exclude(Q(logo_url__isnull=True) | Q(logo_url=""))
        .filter(Q(logo="") | Q(logo__isnull=True))
        .all()[:batch_size]
    ):
        print(f"\nProcessing '{ngo.name}'")

        if not ngo.logo_url.startswith("http"):
            print("... skipped: Logo URL does not start with http")
            continue

        r = requests.get(ngo.logo_url)
        if r.status_code != 200:
            print("... skipped: Request status =", r.status_code)

        ext = mimetypes.guess_extension(r.headers["content-type"])
        with tempfile.TemporaryFile() as fp:
            fp.write(r.content)
            fp.seek(0)
            ngo.logo.save(f"logo{ext}", File(fp))
            print("... new logo:", ngo.logo)


class Command(BaseCommand):
    help = "Import NGO logos from the old storage"

    def handle(self, *args, **options):
        _import_logos()
        self.stdout.write(self.style.SUCCESS("NGO logo import done"))
