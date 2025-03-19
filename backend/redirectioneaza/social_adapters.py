import logging
import re
from typing import Optional

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import pre_social_login, social_account_added, social_account_updated
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from ngohub import NGOHub
from ngohub.exceptions import HubHTTPException
from ngohub.models.organization import Organization, OrganizationBase
from ngohub.models.user import UserProfile
from sentry_sdk import capture_message

from donations.models.ngos import Ngo
from donations.workers.update_organization import create_organization_for_user, update_organization
from users.groups_management import MAIN_ADMIN, NGOHUB_ROLE_TO_REDIRECT_ROLE

logger = logging.getLogger(__name__)

UserModel = get_user_model()


@receiver(social_account_added)
def handle_new_login(sociallogin: SocialLogin, **kwargs) -> None:
    """
    Handler for the social-account-added signal, which is sent for the initial login of a new User.

    We must create a User, an Organization and schedule its data update from NGO Hub.
    """

    common_user_init(sociallogin=sociallogin)


@receiver(social_account_updated)
def handle_existing_login(sociallogin: SocialLogin, **kwargs) -> None:
    """
    Handler for the social-account-update signal, which is sent for all logins after the initial login.

    We already have a User, but we must be sure that the User also has
    an Organization and schedule its data update from NGO Hub.
    """

    common_user_init(sociallogin=sociallogin)


@receiver(pre_social_login)
def handle_pre_social_login(sociallogin: SocialLogin, **kwargs) -> None:
    """
    Handler for the pre-social-login signal, which is sent before the login is actually processed.

    We must make sure that the User is active and has the correct permissions.
    """

    user = sociallogin.user

    if not user:
        return

    if user.is_ngohub_user:
        return check_ngohub_user(sociallogin)

    common_user_init(sociallogin=sociallogin)


class UserOrgAdapter(DefaultSocialAccountAdapter):
    """
    Authentication adapter which makes sure that each new `User` also has an `NGO`
    """

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form=None) -> UserModel:
        """
        Besides the default user creation, also mark this user as coming from NGO Hub,
        update the data with that from NGO Hub.

        If a user with the same email already exists, it will be updated with the new data.
        """

        user_email: str = sociallogin.user.email
        if UserModel.objects.filter(email=user_email).exists():
            user: UserModel = UserModel.objects.get(email=user_email)
        else:
            user: UserModel = super().save_user(request, sociallogin, form)

        user.is_ngohub_user = True
        user.is_verified = True

        user.save()

        common_user_init(sociallogin=sociallogin)

        return user


def check_ngohub_user(sociallogin: SocialLogin) -> None:
    ngohub: NGOHub = NGOHub(settings.NGOHUB_API_HOST)
    user_token: str = sociallogin.token.token

    if not ngohub.check_user_organization_has_application(ngo_token=user_token, login_link=settings.BASE_WEBSITE):
        raise ImmediateHttpResponse(redirect(reverse("error-app-missing")))


def common_user_init(sociallogin: SocialLogin) -> None:
    user: UserModel = sociallogin.user

    user.is_ngohub_user = True
    user.save()

    if user.is_superuser:
        return

    user_token: str = sociallogin.token.token

    ngohub: NGOHub = NGOHub(settings.NGOHUB_API_HOST)

    user_profile: UserProfile = _get_user_profile(ngohub, user, user_token)
    user_role: str = user_profile.role

    _set_user_name(user, user_profile)

    if user_role == settings.NGOHUB_ROLE_SUPER_ADMIN:
        # A super admin from NGO Hub will become a Django admin
        user.is_staff = True
        user.is_superuser = True
        user.save()

        user.groups.add(Group.objects.get(name=MAIN_ADMIN))

        return

    user.is_staff = False
    user.save()

    organization: OrganizationBase = user_profile.organization
    _set_ngo_user(ngohub, user, user_role, user_token, organization)


def _set_ngo_user(
    ngohub: NGOHub,
    user: UserModel,
    user_role: str,
    user_token: str,
    user_organization: OrganizationBase,
) -> None:
    ngohub_org_id = user_organization.id

    if user_role in (settings.NGOHUB_ROLE_NGO_ADMIN, settings.NGOHUB_ROLE_NGO_EMPLOYEE):
        if not ngohub.check_user_organization_has_application(ngo_token=user_token, login_link=settings.BASE_WEBSITE):
            raise ImmediateHttpResponse(redirect(reverse("error-app-missing")))

        user.groups.add(Group.objects.get(name=NGOHUB_ROLE_TO_REDIRECT_ROLE[user_role]))

    else:
        raise ImmediateHttpResponse(redirect(reverse("error-unknown-user-role")))

    _connect_user_and_ngo(user, ngohub_org_id, user_token)


def _set_user_name(user: UserModel, user_profile) -> None:
    changes_made: bool = False
    if not user.first_name:
        user.first_name = user_profile.name
        user.is_verified = True
        changes_made = True

    if user.last_name:
        user.last_name = ""
        changes_made = True

    if changes_made:
        user.save()


def _get_user_profile(ngohub, user: UserModel, user_token) -> UserProfile:
    try:
        user_profile: Optional[UserProfile] = ngohub.get_profile(user_token)
    except HubHTTPException:
        logger.error(f"User {user.email} could not be found in NGO Hub. Please check the configuration.")

        raise ImmediateHttpResponse(redirect(reverse("error-app-missing")))

    return user_profile


def _connect_user_and_ngo(user: UserModel, ngohub_org_id, token) -> None:
    if user.ngo:
        # If the user already has an organization, update it
        user_ngo: Ngo = user.ngo
        user_ngo.ngohub_org_id = ngohub_org_id
        user_ngo.save()

        update_organization(organization_id=user_ngo.pk, token=token)
    else:
        user_ngo: Ngo = _get_or_create_user_ngo(user, ngohub_org_id, token)

    # Make sure the organization is active
    user_ngo.activate()

    user.ngo = user_ngo
    user.save()


def _get_or_create_user_ngo(user: UserModel, ngohub_org_id: int, token: str) -> Ngo:
    """
    If the user does not have an organization, create one with the user as the owner and the data from NGO Hub
    """
    try:
        # NGO exists and has already been imported from NGO Hub
        user_ngo = Ngo.objects.get(ngohub_org_id=ngohub_org_id)
    except Ngo.DoesNotExist:
        hub: NGOHub = NGOHub(settings.NGOHUB_API_HOST)

        ngohub_org_data: Organization = hub.get_organization_profile(ngo_token=token)
        ngo_registration_number: str = ngohub_org_data.general_data.cui

        registration_number_choices = [ngo_registration_number.upper()]
        if re.match(r"[A-Z]{2}\d{2,10}", ngo_registration_number):
            registration_number_choices.append(ngo_registration_number[2:])

        # Check if the NGO already exists in the database by its registration number
        user_ngo_queryset = Ngo.objects.filter(registration_number__in=registration_number_choices)
        if user_ngo_queryset.exists():
            if user_ngo_queryset.count() > 1:
                # If there are multiple NGOs with the same registration number, raise an error and notify admins
                user_email = user.email
                user_pk = user.pk

                _raise_error_multiple_ngos(ngo_registration_number, ngohub_org_id, user_email, user_pk)

            # If there is only one NGO with the registration number, connect the user to it
            user_ngo: Ngo = user_ngo_queryset.first()
            user_ngo.ngohub_org_id = ngohub_org_id
            user_ngo.save()
        else:
            # If the NGO does not exist in the database, create it
            user_ngo: Ngo = create_organization_for_user(user, ngohub_org_data)

    return user_ngo


def _raise_error_multiple_ngos(ngo_registration_number, ngohub_org_id, user_email, user_pk) -> None:
    error_message = (
        f"Multiple organizations with the same registration {ngo_registration_number} found "
        f"for organization with ngohub_org_id {ngohub_org_id} "
        f"and user {user_email} – {user_pk}"
    )
    logger.error(error_message)
    if settings.ENABLE_SENTRY:
        capture_message(error_message, level="error")

    raise ImmediateHttpResponse(redirect(reverse("error-multiple-organizations")))
