from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now
from django_q.tasks import async_task

from donations.models import Donor, Ngo


def _cache_key_for_metric(metric_name: str) -> str:
    """
    Generates a cache key for the given metric name.
    """
    return f"METRIC_{metric_name.upper()}"


def metrics_cache_decorator(func):
    """
    Decorator to cache the metrics functions.
    """

    def wrapper(*args, **kwargs):
        CACHE_KEY = _cache_key_for_metric(func.__name__)

        if cached_result := cache.get(CACHE_KEY):
            # if the cache has expired (the timestamp is older than TIMEOUT_CACHE_NORMAL),
            # we delete the cache entry, trigger an async task to recalculate the metric,
            # and return the cached result; the updated metric will be available in the next request
            cache_timestamp = cached_result.get("timestamp")
            if cache_timestamp and (now() - cache_timestamp).total_seconds() > settings.TIMEOUT_CACHE_NORMAL:
                cache.delete(CACHE_KEY)
                async_task(func.__name__, *args, **kwargs)

            return cached_result
        default_result = {
            "metric": -2,
            "timestamp": now(),
        }

        async_task(func.__name__, *args, **kwargs)

        return default_result

    return wrapper


@metrics_cache_decorator
def current_year_redirections():
    result = {
        "metric": Donor.available.filter(date_created__year=now().year).count(),
        "timestamp": now(),
    }

    cache.set(_cache_key_for_metric("current_year_redirections"), result)

    return result


@metrics_cache_decorator
def all_redirections():
    result = {
        "metric": Donor.available.count(),
        "timestamp": now(),
    }

    cache.set(_cache_key_for_metric("all_redirections"), result)

    return result


@metrics_cache_decorator
def all_active_ngos():
    result = {
        "metric": Ngo.active.count(),
        "timestamp": now(),
    }

    cache.set(_cache_key_for_metric("all_active_ngos"), result)

    return result


@metrics_cache_decorator
def ngos_active_in_current_year():
    result = {
        "metric": Ngo.with_forms_this_year.count(),
        "timestamp": now(),
    }

    cache.set(_cache_key_for_metric("ngos_active_in_current_year"), result)

    return result


@metrics_cache_decorator
def ngos_with_ngo_hub():
    result = {
        "metric": Ngo.ngo_hub.count(),
        "timestamp": now(),
    }

    cache.set(_cache_key_for_metric("ngos_with_ngo_hub"), result)

    return result
