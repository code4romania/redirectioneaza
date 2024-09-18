import logging
from typing import Dict

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import social_account_added
from django.conf import settings
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from ngohub import NGOHub
from ngohub.exceptions import HubHTTPException

from users.groups_management import RESTRICTED_ADMIN

logger = logging.getLogger(__name__)


@receiver(social_account_added)
def handle_new_login(sociallogin: SocialLogin, **kwargs) -> None:
    """
    Handler for the social-account-added signal, which is sent for the initial login of a new User.

    We must create a User, an Organization and schedule its data update from NGO Hub.
    """

    common_user_init(sociallogin=sociallogin)


class UserOrgAdapter(DefaultSocialAccountAdapter):
    """
    Authentication adapter which makes sure that each new `User` also has an `NGO`
    """

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form=None) -> settings.AUTH_USER_MODEL:
        """
        Besides the default user creation, also mark this user as coming from NGO Hub,
        create a blank Organization for them, and schedule a data update from NGO Hub.
        """

        user: settings.AUTH_USER_MODEL = super().save_user(request, sociallogin, form)
        user.is_ngohub_user = True
        user.save()

        common_user_init(sociallogin=sociallogin)

        return user


def common_user_init(sociallogin: SocialLogin) -> settings.AUTH_USER_MODEL:
    user = sociallogin.user
    if user.is_superuser:
        return user

    token: str = sociallogin.token.token

    hub = NGOHub(settings.NGOHUB_API_HOST)

    try:
        user_profile: Dict = hub.get_profile(user_token=token)
    except HubHTTPException:
        user_profile = {}

    user_role: str = user_profile.get("role", "")

    # Check the user role from NGO Hub
    if user_role == settings.NGOHUB_ROLE_SUPER_ADMIN:
        # A super admin from NGO Hub will become a Django admin
        user.first_name = user_profile.get("name", "")
        user.save()

        user.groups.add(Group.objects.get(name=RESTRICTED_ADMIN))

        return None

    # TODO: Implement the following roles when we have the create/update organization tasks
    # elif user_role == settings.NGOHUB_ROLE_NGO_ADMIN:
    #     if not hub.check_user_organization_has_application(ngo_token=token, login_link=settings.BASE_WEBSITE):
    #         if user.is_active:
    #             user.is_active = False
    #             user.save()
    #
    #         raise ImmediateHttpResponse(redirect(reverse("error-app-missing")))
    #     elif not user.is_active:
    #         user.is_active = True
    #         user.save()
    #
    #     # Add the user to the NGO group
    #     user.groups.add(Group.objects.get(name=NGO_ADMIN))
    #
    #     org = Ngo.objects.filter(user=user).first()
    #     if not org:
    #         org = create_blank_org(user)
    #
    #     return org
    #
    # elif user_role == settings.NGOHUB_ROLE_NGO_EMPLOYEE:
    #     # Employees cannot have organizations
    #     raise ImmediateHttpResponse(redirect(reverse("error-user-role")))

    else:
        # Unknown user role
        raise ImmediateHttpResponse(redirect(reverse("error-unknown-user-role")))
