from django.conf import settings
from django.core.cache import cache


def cache_decorator(cache_key_prefix: str, timeout: int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            args_kwargs_key = str(args) + str(kwargs)
            cache_key = f"{cache_key_prefix}_{func.__name__}__{args_kwargs_key}"

            if settings.ENABLE_CACHE:
                sentinel = object()
                cached_value = cache.get(cache_key, sentinel)
                if cached_value is not sentinel:
                    return cached_value

            return_value = func(*args, **kwargs)

            if settings.ENABLE_CACHE:
                cache.set(cache_key, return_value, timeout=timeout)

            return return_value

        return wrapper

    return decorator
