from django.core.cache import cache


def cache_set(key: str, value: dict, timeout: int = None) -> None:
    """
    Sets a value in the cache with a specified key.

    Parameters:
        key (str): The cache key.
        value (dict): The value to cache.
        timeout (int, optional): The cache timeout in seconds. If None, the cache will not expire.
            Defaults to None.
    """
    cache.set(key, value, timeout=timeout)
