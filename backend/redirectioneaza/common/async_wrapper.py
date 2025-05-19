from typing import Any, Callable

from django.conf import settings
from django_q.tasks import async_task


def async_wrapper(
    func: Callable,
    *args: Any,
    **kwargs: Any,
) -> Callable:
    """
    A wrapper function to execute a function either synchronously or asynchronously
    """

    if settings.DEFAULT_RUN_METHOD == "async":
        return async_task(func, *args, **kwargs)

    return func(*args, **kwargs)
