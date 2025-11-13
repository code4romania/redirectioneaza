import logging

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from users.groups_management import USER_GROUPS


class Command(BaseCommand):
    logger = logging.getLogger(__name__)
    _permissions_cache: dict[str, int] = {}

    def handle(self, *args, **kwargs):
        group_names: set[str] = set(USER_GROUPS.keys())
        self.logger.info(f"Creating {len(group_names)} groups: {', '.join(group_names)}.")

        for group_name, group_data in USER_GROUPS.items():
            self._create_group(group_name, group_data)

    def _create_group(self, group_name: str, group_data: dict) -> None:
        users_group: Group
        created: bool
        users_group, created = Group.objects.get_or_create(name=group_name)

        if created:
            self.logger.info(f"Group '{group_name}' was created.")
        else:
            self.logger.info(f"Group '{group_name}' already exists.")

        group_permissions: str | list[str] = group_data.get("permissions")
        if group_permissions == "*":
            permission_ids = Permission.objects.values_list("id", flat=True)
        else:
            permission_ids = self._permission_names_to_ids(group_permissions)

        users_group.permissions.clear()
        users_group.permissions.set(permission_ids)

        success_message: str = f"Group '{group_name}' permissions assigned."
        self.logger.info(success_message)
        self.stdout.write(self.style.SUCCESS(success_message))

    def _permission_names_to_ids(self, group_permissions: list[str]) -> list[int]:
        permission_ids: list[int] = []

        for permission_name in group_permissions:
            if permission_name not in self._permissions_cache:
                try:
                    app_label, permission_label = permission_name.split(".", 1)
                except ValueError:
                    self.logger.warning(f"Permission '{permission_name}' has incorrect naming format.")
                    continue

                try:
                    permission = Permission.objects.get(content_type__app_label=app_label, codename=permission_label)
                except Permission.DoesNotExist:
                    self.logger.warning(f"Permission '{permission_name}' does not exist.")
                    continue
                else:
                    self._permissions_cache[permission_name] = permission.pk

            permission_ids.append(self._permissions_cache[permission_name])

        return permission_ids
