from django.conf import settings
from django.core.cache import cache


def cache_decorator(
    *,
    timeout: int,
    cache_key: str | None = None,
    cache_key_prefix: str | None = None,
    cache_key_custom: str | None = None,
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not cache_key and not cache_key_prefix and not cache_key_custom:
                raise ValueError("Either cache_key, cache_key_prefix, or cache_key_custom must be provided")

            if cache_key:
                _cache_key: str = cache_key
            elif cache_key_custom:
                # noinspection StrFormat
                _cache_key: str = cache_key_custom.format(*args, **kwargs)
            else:
                cache_suffix = (
                    hash(f"{func.__name__}__{str(args)}_{str(kwargs)}")
                    .to_bytes(length=8, byteorder="big", signed=True)
                    .hex()
                )
                _cache_key: str = f"{cache_key_prefix}__{cache_suffix}"

            if settings.ENABLE_CACHE:
                sentinel = object()
                cached_value = cache.get(_cache_key, sentinel)
                if cached_value is not sentinel:
                    return cached_value

            return_value = func(*args, **kwargs)

            if settings.ENABLE_CACHE:
                cache.set(cache_key, return_value, timeout=timeout)

            return return_value

        return wrapper

    return decorator
