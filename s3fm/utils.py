"""Module contains common helper functions."""
import os
import signal

import psutil


def kill_child_processes() -> None:
    """Kill all spawned child processes.

    This is mainly used to have a grace exit experience when
    the app is still loading and waiting for a long running task
    created by ProcessPoolExecutor.

    source: https://stackoverflow.com/a/45515052
    """
    parent_pid = os.getpid()
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(signal.SIGTERM)
