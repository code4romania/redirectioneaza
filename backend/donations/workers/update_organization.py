import logging
import mimetypes
import random
import string
import tempfile
from typing import Dict, List, Optional, Union

import requests
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from django_q.tasks import async_task
from ngohub import NGOHub
from ngohub.models.organization import Organization, OrganizationGeneral
from pycognito import Cognito
from requests import Response

from donations.common.validation.clean_slug import clean_slug
from donations.common.validation.validate_slug import NgoSlugValidator
from donations.models.ngos import Ngo
from redirectioneaza.common.cache import cache_decorator

logger = logging.getLogger(__name__)


def remove_signature(s3_url: str) -> str:
    """
    Extract the S3 file name without the URL signature and the directory path
    """
    if s3_url:
        return s3_url.split("?")[0].split("/")[-1]
    else:
        return ""


def copy_file_to_organization(ngo: Ngo, signed_file_url: str, file_type: str):
    if not hasattr(ngo, file_type):
        raise AttributeError(f"Organization has no attribute '{file_type}'")

    filename: str = remove_signature(signed_file_url)
    if not filename and getattr(ngo, file_type):
        getattr(ngo, file_type).delete()
        error_message = f"ERROR: {file_type.upper()} file URL is empty, deleting the existing file."
        logger.warning(error_message)
        return error_message

    if not filename:
        error_message = f"ERROR: {file_type.upper()} file URL is empty, but is a required field."
        logger.warning(error_message)
        return error_message

    if filename == ngo.filename_cache.get(file_type, ""):
        logger.info(f"{file_type.upper()} file is already up to date.")
        return None

    r: Response = requests.get(signed_file_url)
    if r.status_code != requests.codes.ok:
        logger.info(f"{file_type.upper()} file request status = {r.status_code}")
        error_message = f"ERROR: Could not download {file_type} file from NGO Hub, error status {r.status_code}."
        logger.warning(error_message)
        return error_message

    extension: str = mimetypes.guess_extension(r.headers["content-type"])

    # TODO: mimetypes thinks that some S3 documents are .bin files, which is useless
    if extension == ".bin":
        extension = ""
    with tempfile.TemporaryFile() as fp:
        fp.write(r.content)
        fp.seek(0)
        getattr(ngo, file_type).save(f"{file_type}{extension}", File(fp))

    ngo.filename_cache[file_type] = filename


@cache_decorator(timeout=settings.TIMEOUT_CACHE_NORMAL, cache_key="authenticate_with_ngohub")
def authenticate_with_ngohub() -> str:
    u = Cognito(
        user_pool_id=settings.AWS_COGNITO_USER_POOL_ID,
        client_id=settings.AWS_COGNITO_CLIENT_ID,
        client_secret=settings.AWS_COGNITO_CLIENT_SECRET,
        username=settings.NGOHUB_API_ACCOUNT,
        user_pool_region=settings.AWS_COGNITO_REGION,
    )
    u.authenticate(password=settings.NGOHUB_API_KEY)

    return u.id_token


def get_ngo_hub_data(ngohub_org_id: int, token: str = "") -> Organization:
    hub = NGOHub(settings.NGOHUB_API_HOST)

    # if a token is already provided, use it for the profile endpoint
    if token:
        return hub.get_organization_profile(ngo_token=token)

    # if no token is provided, attempt to authenticate as an admin for the organization endpoint
    token: str = authenticate_with_ngohub()
    return hub.get_organization(organization_id=ngohub_org_id, admin_token=token)


def update_local_ngo_with_ngohub_data(ngo: Ngo, ngohub_ngo: Organization) -> Dict[str, Union[int, List[str]]]:
    errors: List[str] = []

    if not ngo.filename_cache:
        ngo.filename_cache = {}

    ngohub_general_data: OrganizationGeneral = ngohub_ngo.general_data

    ngo.name = ngohub_general_data.alias or ngohub_general_data.name

    if not ngo.slug:
        new_slug = clean_slug(ngo.name)
        if NgoSlugValidator.is_blocked(new_slug):
            random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
            new_slug = f"{new_slug}-{random_string}"
        elif NgoSlugValidator.is_reused_by_ngo(new_slug, ngo.pk):
            random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
            new_slug = f"{new_slug}-{random_string}"
        ngo.slug = new_slug

    if ngo.description is None:
        ngo.description = ngohub_general_data.description or ""

    ngo.registration_number = ngohub_general_data.cui

    # Import the organization logo
    logo_url: str = ngohub_general_data.logo
    logo_url_error: Optional[str] = copy_file_to_organization(ngo, logo_url, "logo")
    if logo_url_error:
        errors.append(logo_url_error)

    # TODO: the county and active region have different formats here
    ngo.address = ngohub_general_data.address
    ngo.locality = ngohub_general_data.city.name
    ngo.county = ngohub_general_data.county.name

    active_region: str = ngohub_ngo.activity_data.area
    if ngohub_ngo.activity_data.area == "Regional":
        regions: List[str] = [region.name for region in ngohub_ngo.activity_data.regions]
        active_region = f"{ngohub_ngo.activity_data.area} ({','.join(regions)})"
    elif ngohub_ngo.activity_data.area == "Local":
        counties: List[str] = [city.county.name for city in ngohub_ngo.activity_data.cities]
        active_region = f"{ngohub_ngo.activity_data.area} ({','.join(counties)})"
    ngo.active_region = active_region

    ngo.phone = ngohub_general_data.phone
    ngo.email = ngohub_general_data.email
    ngo.website = ngohub_general_data.website or ""

    ngo.is_social_service_viable = ngohub_ngo.activity_data.is_social_service_viable
    ngo.is_verified = True

    ngo.ngohub_last_update_ended = timezone.now()
    ngo.save()

    task_result: Dict = {
        "ngo_id": ngo.id,
        "errors": errors,
    }

    return task_result


def update_organization_process(organization_id: int, token: str = "") -> Dict[str, Union[int, List[str]]]:
    """
    Update the organization with the given ID.
    """
    ngo: Ngo = Ngo.objects.get(pk=organization_id)

    ngo.ngohub_last_update_started = timezone.now()
    ngo.save()

    ngohub_id: int = ngo.ngohub_org_id
    ngohub_org_data: Organization = get_ngo_hub_data(ngohub_id, token)

    task_result = update_local_ngo_with_ngohub_data(ngo, ngohub_org_data)

    return task_result


def update_organization(organization_id: int, update_method: str = None, token: str = ""):
    """
    Update the organization with the given ID asynchronously.
    """
    update_method = update_method or settings.UPDATE_ORGANIZATION_METHOD
    if update_method == "async":
        async_task(update_organization_process, organization_id, token)
    else:
        update_organization_process(organization_id, token)


def create_organization_for_user(user, ngohub_org_data: Organization) -> Ngo:
    """
    Create a blank organization for the given user.
    The data regarding the organization will be added from NGO Hub.
    """
    ngo = Ngo(registration_number=ngohub_org_data.general_data.cui, ngohub_org_id=ngohub_org_data.id)
    ngo.save()

    update_local_ngo_with_ngohub_data(ngo, ngohub_org_data)

    user.ngo = ngo
    user.save()

    return ngo
