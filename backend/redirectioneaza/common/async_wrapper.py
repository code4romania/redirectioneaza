from collections.abc import Callable
from typing import Any

from django.conf import settings
from django_q.tasks import async_task


def async_wrapper(
    func: Callable,
    *,
    async_flag: str = None,
    **kwargs: Any,
) -> Callable:
    """
    A wrapper function to execute a function either synchronously or asynchronously
    func: Callable
        The function to be executed
    async_wrapper: str, optional
        A string to determine the execution method. If None, uses the default from settings.DEFAULT_RUN_METHOD
    **kwargs: Any
        Keyword arguments to pass to the function

    Returns:
        The result of the function execution
    """

    run_method: str = async_flag if async_flag else settings.DEFAULT_RUN_METHOD

    if run_method == "async":
        return async_task(func, **kwargs)

    return func(**kwargs)
