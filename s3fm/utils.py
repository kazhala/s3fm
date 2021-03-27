"""Internal helper functions for `s3fm`.

These helper functions are standalong functions that
have no dependency or interaction with `prompt_toolkit`.
"""
import asyncio
import shutil
from functools import partial
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Tuple

from prompt_toolkit.application import run_in_terminal


def get_dimension(offset: int = 0) -> Tuple[int, int]:
    """Get terminal dimensions.

    Args:
        offset: Additional offset to put against the height and width.

    Returns:
        Height and width of the terminal with additional offset.
    """
    term_cols, term_rows = shutil.get_terminal_size()
    return term_cols - offset, term_rows - offset


def transform_async(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """Transform a standard blocking call to async call.

    Args:
        func: The function to transform.

    Returns:
        Transformed function.

    Reference:
        https://github.com/Tinche/aiofiles/blob/32e3a7346b8a4060efb6102afdf9c3398b19030f/aiofiles/os.py#L7
    """

    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_running_loop()
        partial_func = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, partial_func)

    return run


def human_readable_size(value: float) -> Optional[str]:
    """Convert bytes to human readable size.

    Args:
        value: Value in bytes.

    Returns:
        Humand readable size.

    Reference:
        https://github.com/aws/aws-cli
    """
    HUMANIZE_SUFFIXES = ("K", "M", "G", "T", "P", "E")
    base = 1024
    bytes_int = float(value)

    if bytes_int < base:
        return "%d B" % bytes_int

    for i, suffix in enumerate(HUMANIZE_SUFFIXES):
        unit = base ** (i + 2)
        if round((bytes_int / unit) * base) < base:
            return "%.1f %s" % ((base * bytes_int / unit), suffix)


def patched_print(*values) -> None:
    """Print the values without interrupting the prompt."""

    def _print():
        print(*values)

    run_in_terminal(_print)
