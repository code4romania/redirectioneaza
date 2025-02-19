import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class CommonCreateUserCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Username of the superuser (default: email)",
            required=False,
        )
        parser.add_argument(
            "--first_name",
            type=str,
            help="First name of the superuser",
            required=False,
        )
        parser.add_argument(
            "--last_name",
            type=str,
            help="Last name of the superuser",
            required=False,
        )

    @classmethod
    def _get_or_create_user(
        cls,
        new_email: str,
        password: str,
        is_superuser: bool,
        is_staff: bool,
        first_name: str = "Admin",
        last_name: str = "Admin",
    ):
        if not password:
            raise ValueError("Password is required. Please set the proper variables.")

        user_model = get_user_model()

        if user_model.objects.filter(email=new_email).exists():
            if user_model.objects.filter(email=new_email).count() > 1:
                logger.error("There are multiple users with the same email. Please fix it.")
                return None

            return user_model.objects.get(email=new_email)

        user = user_model(
            email=new_email,
            username=new_email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_superuser=is_superuser,
            is_staff=is_staff,
        )
        user.set_password(password)

        user.save()

        logger.info("Super admin created successfully")

        return user
