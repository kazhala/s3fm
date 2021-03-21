"""Module contains the :class:`History` class.

Used to store and retrieve the state of the :class:`~s3fm.app.App`.
"""
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterator, Tuple

from s3fm.id import ID, Pane, PaneMode

__all__ = ["History"]


class Directory(OrderedDict):
    """Custom :class:`collections.OrderedDict` with size limit.

    Used to store directory history.

    Args:
        size_limit: The max size of the dict.
    """

    def __init__(self, size_limit, *args, **kwds) -> None:
        self._size_limit = size_limit
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value) -> None:
        if key in self:
            self.move_to_end(key, last=True)
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self) -> None:
        if self._size_limit is not None:
            while len(self) > self._size_limit:
                self.popitem(last=False)


class History:
    """Used for storing and reading history.

    Cache user activity and also store/retrieve these info
    into history files on application exit.
    """

    def __init__(self, max_size=500) -> None:
        self._left_mode = PaneMode.s3
        self._left_path = ""
        self._right_mode = PaneMode.fs
        self._right_path = str(Path.cwd())
        self._focus = Pane.left
        self._directory = Directory(size_limit=max_size or 500)

    async def read(self) -> None:
        """Read history."""
        self._left_mode = PaneMode.s3
        self._right_mode = PaneMode.fs
        self._focus = Pane.left

    def write(self) -> None:
        """Write history."""
        if sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            base_dir = os.getenv("XDG_DATA_HOME", "~/.local/share")
            hist_dir = Path("%s/s3fm" % base_dir).expanduser()
            if not hist_dir.exists():
                hist_dir.mkdir(parents=True)
            hist_file = hist_dir.joinpath("history.json")
        else:
            # TODO: get windows config
            base_dir = os.getenv("APPDATA")
            hist_file = Path("%s\\s3fm\\history\\history.json" % base_dir).expanduser()
        with hist_file.open("w") as file:
            json.dump(dict(self), file, indent=4)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """Override __iter__ to allow dict representation."""
        for attr, value in self.__dict__.items():
            yield attr, value

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
