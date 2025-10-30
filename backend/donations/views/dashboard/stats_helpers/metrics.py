from typing import Any, Dict

from django.utils.timezone import now

from donations.models import Donor, Ngo
from donations.views.dashboard.stats_helpers.utils import cache_set

# Cache key prefix for metrics
METRIC_CACHE_PREFIX = "METRIC_"


def _cache_key_for_metric(metric_name: str) -> str:
    """
    Generates a cache key for the given metric name.
    """
    return f"{METRIC_CACHE_PREFIX}{metric_name.upper()}"


# TODO: smart cache this
def current_year_redirections() -> Dict[str, Any]:
    """
    Returns the number of redirections (donations) for the current year.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    return _update_current_year_redirections()


def _update_current_year_redirections(_cache_key: str = None, _timeout: int = None) -> Dict[str, Any]:
    """
    Updates the number of redirections for the current year and caches the result.

    Parameters:
        _cache_key (str, optional): The cache key to use when storing the result.
            This is passed by the cache.
        _timeout (int, optional): The cache timeout in seconds.
            This is passed by the cache.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    result = {
        "metric": Donor.available.filter(date_created__year=now().year).count(),
        "timestamp": now(),
    }

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, result, timeout=_timeout)

    return result


# TODO: smart cache this
def all_redirections() -> Dict[str, Any]:
    """
    Returns the total number of redirections (donations) across all years.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    return _update_all_redirections()


def _update_all_redirections(_cache_key: str = None, _timeout: int = None) -> Dict[str, Any]:
    """
    Updates the total number of redirections and caches the result.

    Parameters:
        _cache_key (str, optional): The cache key to use when storing the result.
            This is passed by the cache.
        _timeout (int, optional): The cache timeout in seconds.
            This is passed by the cache.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    result = {
        "metric": Donor.available.count(),
        "timestamp": now(),
    }

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, result, timeout=_timeout)

    return result


# TODO: smart cache this
def all_active_ngos() -> Dict[str, Any]:
    """
    Returns the total number of active NGOs.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    return _update_all_active_ngos()


def _update_all_active_ngos(_cache_key: str = None, _timeout: int = None) -> Dict[str, Any]:
    """
    Updates the total number of active NGOs and caches the result.

    Parameters:
        _cache_key (str, optional): The cache key to use when storing the result.
            This is passed by the cache.
        _timeout (int, optional): The cache timeout in seconds.
            This is passed by the cache.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    result = {
        "metric": Ngo.active.count(),
        "timestamp": now(),
    }

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, result, timeout=_timeout)

    return result


# TODO: smart cache this
def ngos_active_in_current_year() -> Dict[str, Any]:
    """
    Returns the number of NGOs that are active in the current year.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    return _update_ngos_active_in_current_year()


def _update_ngos_active_in_current_year(_cache_key: str = None, _timeout: int = None) -> Dict[str, Any]:
    """
    Updates the number of NGOs active in the current year and caches the result.

    Parameters:
        _cache_key (str, optional): The cache key to use when storing the result.
            This is passed by the cache.
        _timeout (int, optional): The cache timeout in seconds.
            This is passed by the cache.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    result = {
        "metric": Ngo.with_forms_this_year.count(),
        "timestamp": now(),
    }

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, result, timeout=_timeout)

    return result


# TODO: smart cache this
def ngos_with_ngo_hub() -> Dict[str, Any]:
    """
    Returns the number of NGOs that are part of the NGO Hub.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    return _update_ngos_with_ngo_hub()


def _update_ngos_with_ngo_hub(_cache_key: str = None, _timeout: int = None) -> Dict[str, Any]:
    """
    Updates the number of NGOs with NGO Hub and caches the result.

    Parameters:
        _cache_key (str, optional): The cache key to use when storing the result.
            This is passed by the cache.
        _timeout (int, optional): The cache timeout in seconds.
            This is passed by the cache.

    Returns:
        Dict[str, Any]: A dictionary containing the metric and timestamp.
    """
    result = {
        "metric": Ngo.ngo_hub.count(),
        "timestamp": now(),
    }

    if _cache_key and _timeout is not None:
        cache_set(_cache_key, result, timeout=_timeout)

    return result
