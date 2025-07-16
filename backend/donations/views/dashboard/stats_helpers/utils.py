from django.core.cache import cache


def cache_set(key: str, value: dict) -> None:
    """
    Sets a value in the cache with a specified key.
    The timeout is set to None, meaning the cache will not expire.
    """
    cache.set(key, value, timeout=None)
