"""Module contains the file object and helper methods."""
from typing import Callable, NamedTuple

from s3fm.id import ID

File = NamedTuple(
    "File",
    [("name", str), ("type", ID), ("info", str), ("hidden", bool), ("index", int)],
)


def file_action(func: Callable[[File], None]) -> Callable[[File], None]:
    """Decorate a method related to file action.

    On loading time, :attr:`~s3fm.ui.filepane.FilePane.current_selection`
    may not exist and raise :obj:`IndexError`. Using this decorator
    to perform additional checks.

    Args:
        func: The function to decorate.

    Returns:
        Updated function with checks.
    """

    def executable(file: File):
        if not file:
            return
        func(file)

    return executable
