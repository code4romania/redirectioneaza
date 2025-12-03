import logging
import mimetypes
import random
import string
import tempfile

import requests
from django.conf import settings
from django.core.files import File
from django.db import DatabaseError
from django.utils import timezone
from django.utils.text import slugify
from django_q.tasks import async_task
from ngohub import NGOHub
from ngohub.models.organization import Organization, OrganizationGeneral
from pycognito import Cognito
from requests import Response

from donations.common.validation.validate_slug import NgoSlugValidator
from donations.models.common import CommonFilenameCacheModel
from donations.models.ngos import Cause, Ngo
from redirectioneaza.common.cache import cache_decorator

logger = logging.getLogger(__name__)


def _remove_signature(s3_url: str) -> str:
    """
    Extract the S3 file name without the URL signature and the directory path
    """
    if s3_url:
        return s3_url.split("?")[0].split("/")[-1]

    return ""


def _copy_file_to_object_with_filename_cache(
    target_object: CommonFilenameCacheModel,
    signed_file_url: str,
    attribute_name: str,
):
    if not hasattr(target_object, attribute_name):
        raise AttributeError(f"Target object {target_object} has no attribute '{attribute_name}'")

    filename: str = _remove_signature(signed_file_url)
    if not filename and getattr(target_object, attribute_name):
        getattr(target_object, attribute_name).delete()
        error_message = f"ERROR: {attribute_name.upper()} file URL is empty, deleting the existing file."
        logger.warning(error_message)
        return error_message

    if not filename:
        error_message = f"ERROR: {attribute_name.upper()} file URL is empty, but is a required field."
        logger.warning(error_message)
        return error_message

    if filename == target_object.filename_cache.get(attribute_name, ""):
        logger.info(f"{attribute_name.upper()} file is already up to date.")
        return None

    r: Response = requests.get(signed_file_url)
    if r.status_code != requests.codes.ok:
        logger.info(f"{attribute_name.upper()} file request status = {r.status_code}")
        error_message = f"ERROR: Could not download {attribute_name} file from NGO Hub, error status {r.status_code}."
        logger.warning(error_message)
        return error_message

    extension: str = filename.split(".")[-1]
    if not extension or len(extension) > 4:
        extension: str = mimetypes.guess_extension(r.headers["content-type"])

        if extension == ".bin":
            logger.warning(f"Could not get extension for attribute {attribute_name.upper()} for object {target_object}")
            extension = ""

    with tempfile.TemporaryFile() as fp:
        fp.write(r.content)
        fp.seek(0)
        getattr(target_object, attribute_name).save(f"{attribute_name}{extension}", File(fp))

    target_object.filename_cache[attribute_name] = filename


@cache_decorator(timeout=settings.TIMEOUT_CACHE_NORMAL, cache_key="authenticate_with_ngohub")
def _authenticate_with_ngohub() -> str:
    u = Cognito(
        user_pool_id=settings.AWS_COGNITO_USER_POOL_ID,
        client_id=settings.AWS_COGNITO_CLIENT_ID,
        client_secret=settings.AWS_COGNITO_CLIENT_SECRET,
        username=settings.NGOHUB_API_ACCOUNT,
        user_pool_region=settings.AWS_COGNITO_REGION,
    )
    u.authenticate(password=settings.NGOHUB_API_KEY)

    return u.id_token


def _get_ngo_hub_data(ngohub_org_id: int, token: str = "") -> Organization:
    hub = NGOHub(settings.NGOHUB_API_HOST)

    # if a token is already provided, use it for the profile endpoint
    if token:
        return hub.get_organization_profile(ngo_token=token)

    # if no token is provided, attempt to authenticate as an admin for the organization endpoint
    token: str = _authenticate_with_ngohub()
    return hub.get_organization(organization_id=ngohub_org_id, admin_token=token)


def _update_main_cause_of_ngo(ngo: Ngo, ngohub_general_data: OrganizationGeneral) -> list[str] | Cause:
    try:
        cause: Cause = ngo.causes.get(is_main=True)
    except Cause.DoesNotExist:
        logger.exception("Main cause does not exist, creating a new one.")
        cause = _create_main_cause(ngo, ngohub_general_data)

    return _update_main_cause(cause, ngohub_general_data)


def _update_main_cause(cause: Cause, ngohub_general_data: OrganizationGeneral) -> list[str] | Cause:
    errors = []

    logo_url_error: str | None = _copy_file_to_object_with_filename_cache(
        cause,
        ngohub_general_data.logo,
        "display_image",
    )
    if logo_url_error:
        errors.append(logo_url_error)

    cause.save()

    if errors:
        logger.warning(f"Errors while updating the logo: {errors}")
        return errors

    return cause


def _create_main_cause(ngo: Ngo, ngohub_general_data: OrganizationGeneral) -> Cause:
    cause: Cause = Cause(ngo=ngo, is_main=True)

    cause.name = ngohub_general_data.alias or ngohub_general_data.name
    cause.description = ngohub_general_data.description

    new_slug: str = slugify(ngo.name).replace("_", "-")
    if NgoSlugValidator.is_blocked(new_slug) or NgoSlugValidator.is_reused(new_slug):
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        new_slug = f"{new_slug}-{random_string}"

    cause.slug = new_slug

    cause.save()

    return cause


def _update_local_ngo_with_ngohub_data(ngo: Ngo, ngohub_ngo: Organization) -> dict[str, int | list[str]]:
    errors: list[str] = []

    if not ngo.filename_cache:
        ngo.filename_cache = {}

    ngohub_general_data: OrganizationGeneral = ngohub_ngo.general_data

    ngo.name = ngohub_general_data.name

    ngo.registration_number = ngohub_general_data.cui

    # TODO: the county and active region have different formats here
    ngo.address = ngohub_general_data.address
    ngo.locality = ngohub_general_data.city.name
    ngo.county = ngohub_general_data.county.name

    active_region: str = ngohub_ngo.activity_data.area
    if ngohub_ngo.activity_data.area == "Regional":
        regions: list[str] = [region.name for region in ngohub_ngo.activity_data.regions]
        active_region = f"{ngohub_ngo.activity_data.area} ({','.join(regions)})"
    elif ngohub_ngo.activity_data.area == "Local":
        counties: list[str] = [city.county.name for city in ngohub_ngo.activity_data.cities]
        active_region = f"{ngohub_ngo.activity_data.area} ({','.join(counties)})"
    ngo.active_region = active_region

    ngo.phone = ngohub_general_data.phone
    ngo.email = ngohub_general_data.email
    ngo.website = ngohub_general_data.website or ""

    ngo.is_social_service_viable = ngohub_ngo.activity_data.is_social_service_viable
    ngo.is_verified = True
    ngo.save()

    if not ngo.causes.exists():
        main_cause = _create_main_cause(ngo, ngohub_general_data)
        main_cause_update_result = _update_main_cause(main_cause, ngohub_general_data)
    else:
        main_cause_update_result = _update_main_cause_of_ngo(ngo, ngohub_general_data)

    if isinstance(main_cause_update_result, list):
        errors.extend(main_cause_update_result)

    ngo.ngohub_last_update_ended = timezone.now()
    ngo.save()

    task_result: dict = {
        "ngo_id": ngo.id,
        "errors": errors,
    }

    return task_result


def _update_organization_task(organization_id: int, token: str = "") -> dict[str, int | list[str]]:
    """
    Update the organization with the given ID.
    """
    last_update_start = timezone.now()

    ngo: Ngo = Ngo.objects.get(pk=organization_id)

    ngo.ngohub_last_update_started = last_update_start
    ngo.save()

    ngohub_id: int = ngo.ngohub_org_id
    ngohub_org_data: Organization = _get_ngo_hub_data(ngohub_id, token)

    task_result = _update_local_ngo_with_ngohub_data(ngo, ngohub_org_data)

    return task_result


def update_organization(organization_id: int, update_method: str | None = None, token: str = ""):
    """
    Update the organization with the given ID asynchronously.
    """
    update_method = update_method or settings.UPDATE_ORGANIZATION_METHOD
    function_args = [organization_id, token]
    if update_method == "async":
        async_task(_update_organization_task, *function_args)
    else:
        _update_organization_task(*function_args)


def create_organization_for_user(user, ngohub_org_data: Organization) -> Ngo:
    """
    Create a blank organization for the given user.
    The data regarding the organization will be added from NGO Hub.
    """
    ngo = Ngo(registration_number=ngohub_org_data.general_data.cui, ngohub_org_id=ngohub_org_data.id)
    ngo.save()

    try:
        _update_local_ngo_with_ngohub_data(ngo, ngohub_org_data)
    except DatabaseError as e:
        logger.exception(
            f"Database error while creating NGO for user {user.id} with NGO Hub ID {ngohub_org_data.id}:\n{e}"
        )
        ngo.delete()
        raise e

    user.ngo = ngo
    user.save()

    return ngo
