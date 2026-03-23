import json
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django_q.tasks import async_task

from donations.models.ngos import Ngo
from utils.helper_logging import setup_logger

logger = setup_logger(__name__)


def _get_cult_registry_data(registration_numbers: list[str]):
    if not registration_numbers:
        return {"present": [], "absent": [], "error": False}

    if len(registration_numbers) > 500:
        logger.warning("Only the first 500 registration numbers will be checked in ANAF Cult Registry")
        registration_numbers = registration_numbers[:500]

    yesterday = timezone.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")

    headers = {"Content-Type": "application/json"}
    payload = [{"cui": registration_number, "data": date_str} for registration_number in registration_numbers]

    r = requests.post(settings.ANAF_CULT_REGISTRY_ENDPOINT, headers=headers, data=json.dumps(payload))
    if r.status_code != 200:
        logger.warning("Failed to check ANAF Cult Registry for: %s", " ".join(registration_numbers))
        return {"present": [], "absent": [], "error": True}

    present_registration_numbers = []
    absent_registration_numbers = []
    for f in r.json().get("found", []):
        if f.get("statusRegCult"):
            present_registration_numbers.append(f.get("cui"))
        else:
            absent_registration_numbers.append(f.get("cui"))

    return {"present": present_registration_numbers, "absent": absent_registration_numbers, "error": False}


def _check_organizations_task(registration_numbers: list[str]) -> dict[str, int | list[str]]:
    """
    Check the organizations with the given ID.
    """
    Ngo.objects.filter(registration_number__in=registration_numbers).update(cult_registry_check_started=timezone.now())

    try:
        anaf_data = _get_cult_registry_data(registration_numbers)
    except Exception as e:
        logger.exception(f"Error while fetching ANAF data:\n{e}")
        return {
            "errors": [f"Error while fetching ANAF data:\n{e}"],
        }

    Ngo.objects.filter(registration_number__in=anaf_data.get("present", [])).update(
        cult_registry_check_ended=timezone.now(), is_in_cult_registry=True
    )
    Ngo.objects.filter(registration_number__in=anaf_data.get("absent", [])).update(
        cult_registry_check_ended=timezone.now(), is_in_cult_registry=False
    )

    task_result = {}  # TODO

    return task_result


def cult_registry_check_organizations(id_registration_numbers: list[str], update_method: str | None = None):
    """
    Update the organization with the given ID asynchronously.
    """
    logger.info(
        f"Starting ANAF checking for organizations "
        f"using method '{update_method or settings.UPDATE_ORGANIZATION_METHOD}'"
    )

    update_method = update_method or settings.UPDATE_ORGANIZATION_METHOD
    function_args = [
        id_registration_numbers,
    ]
    if update_method == "async":
        async_task(_check_organizations_task, *function_args)
        task_result = {"status": "Task started asynchronously."}
    else:
        task_result = _check_organizations_task(*function_args)

    return task_result
