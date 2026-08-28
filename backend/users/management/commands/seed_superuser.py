import logging

from django.conf import settings
from django.contrib.auth.models import Group

from users.groups_management import MAIN_ADMIN

from ._private.seed_user import CommonCreateUserCommand

logger = logging.getLogger(__name__)


class Command(CommonCreateUserCommand):
    help = "Command to create a superuser"

    def handle(self, *args, **kwargs):
        kwargs["last_name"] = "Super"
        kwargs["first_name"] = "User"

        super_admin = self._get_or_create_user(
            new_email=settings.DJANGO_ADMIN_EMAIL,
            password=settings.DJANGO_ADMIN_PASSWORD,
            is_superuser=True,
            is_staff=True,
            first_name=kwargs.get("first_name", ""),
            last_name=kwargs.get("last_name", ""),
        )
        logger.info("Super admin created successfully")

        admin_group = Group.objects.get(name=MAIN_ADMIN)
        super_admin.groups.add(admin_group)

        return 0
