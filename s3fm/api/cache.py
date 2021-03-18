"""Module contains the :class:`Cache` class.

Used to store and retrieve the state of the :class:`~s3fm.app.App`.
"""
from pathlib import Path

from s3fm.id import ID, Pane, PaneMode


class Cache:
    """Used for storing and reading cache.

    Cache user activity and also store/retrieve these info
    into cache files on application exit.
    """

    def __init__(self) -> None:
        self._left_mode = PaneMode.s3
        self._left_path = ""
        self._right_mode = PaneMode.fs
        self._right_path = str(Path.cwd())
        self._focus = Pane.left
        self._directory = {}

    async def read_cache(self) -> None:
        """Read cache."""
        self._left_mode = PaneMode.s3
        self._right_mode = PaneMode.fs
        self._focus = Pane.left

    @property
    def focus(self) -> ID:
        """:ref:`pages/configuration:ID`: Current :class:`~s3fm.app.App` focus id."""
        return self._focus

    @property
    def left_mode(self) -> ID:
        """:ref:`pages/configuration:ID`: Left pane mode."""
        return self._left_mode

    @property
    def right_mode(self) -> ID:
        """:ref:`pages/configuration:ID`: Right pane mode."""
        return self._right_mode
