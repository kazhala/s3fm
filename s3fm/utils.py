"""Internal helper functions for `s3fm`.

These helper functions are standalong functions that
have no dependency or interaction with `prompt_toolkit`.
"""
import os
import shutil
import signal
from typing import Tuple

import psutil


def kill_child_processes() -> None:
    """Kill all spawned child processes.

    This is mainly used to have a grace force exit experience when
    the app is still loading and waiting for a long running task
    created by :obj:`concurrent.futures.ProcessPoolExecutor`.

    Reference:
        https://stackoverflow.com/a/45515052
    """
    parent_pid = os.getpid()
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(signal.SIGTERM)


def get_dimension(offset: int = 0) -> Tuple[int, int]:
    """Get terminal dimensions.

    Args:
        offset: Additional offset to put against the height and width.

    Returns:
        Height and width of the terminal with additional offset.
    """
    term_cols, term_rows = shutil.get_terminal_size()
    return term_cols - offset, term_rows - offset
