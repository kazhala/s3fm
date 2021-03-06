"""Module contains the :class:`History` class.

Used to store and retrieve the state of the :class:`~s3fm.app.App`.
"""
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterator, Tuple

from s3fm.enums import LayoutMode, Pane, PaneMode
from s3fm.utils import transform_async

__all__ = ["History"]


class Directory(OrderedDict):
    """Custom :class:`collections.OrderedDict` with size limit.

    Used to store directory history.

    Args:
        size_limit: The max size of the dict.

    Reference:
        https://stackoverflow.com/a/2437645
    """

    def __init__(self, *args, **kwargs) -> None:
        self._size_limit = kwargs.pop("size_limit")
        super().__init__(*args, **kwargs)
        self._check_size_limit()

    def __setitem__(self, key, value) -> None:
        if key in self:
            self.move_to_end(key, last=True)
        super().__setitem__(key, value)
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

    def __init__(self, dir_max_size=500, cmd_max_size=500) -> None:
        self._layout = LayoutMode.vertical
        self._left_mode = PaneMode.s3
        self._left_path = ""
        self._left_index = 0
        self._right_mode = PaneMode.fs
        self._right_path = str(Path.cwd())
        self._right_index = 0
        self._focus = Pane.left
        self._dir_max_size = dir_max_size
        self._cmd_max_size = cmd_max_size
        self._directory = Directory(size_limit=self._dir_max_size or 500)
        self._cmd = []

    @transform_async
    def read(self) -> None:
        """Read history."""
        if not self.hist_file.exists():
            return
        attrs = dict(self)
        with self.hist_file.open("r") as file:
            result = json.load(file)
            for key, value in result.items():
                if key == "_directory":
                    self._directory = Directory(value, size_limit=self._dir_max_size)
                elif key in attrs:
                    setattr(self, key, value)

    def write(self) -> None:
        """Write history."""
        with self.hist_file.open("w") as file:
            json.dump(dict(self), file, indent=4)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """Override __iter__ to allow dict representation."""
        for attr, value in self.__dict__.items():
            yield attr, value

    @property
    def focus(self) -> Pane:
        """Pane: Current focus pane."""
        return self._focus

    @focus.setter
    def focus(self, value: Pane) -> None:
        self._focus = value

    @property
    def left_mode(self) -> PaneMode:
        """PaneMode: Left pane mode."""
        return self._left_mode

    @left_mode.setter
    def left_mode(self, value: PaneMode) -> None:
        self._left_mode = value

    @property
    def right_mode(self) -> PaneMode:
        """PaneMode: Right pane mode."""
        return self._right_mode

    @right_mode.setter
    def right_mode(self, value: PaneMode) -> None:
        self._right_mode = value

    @property
    def left_index(self) -> int:
        """int: Left selection index."""
        return self._left_index

    @left_index.setter
    def left_index(self, value: int) -> None:
        self._left_index = value

    @property
    def right_index(self) -> int:
        """int: Right selection index."""
        return self._right_index

    @right_index.setter
    def right_index(self, value: int) -> None:
        self._right_index = value

    @property
    def left_path(self) -> str:
        """str: Left filepath."""
        return self._left_path

    @left_path.setter
    def left_path(self, value: str) -> None:
        self._left_path = value

    @property
    def right_path(self) -> str:
        """str: Right filepath."""
        return self._right_path

    @right_path.setter
    def right_path(self, value: str) -> None:
        self._right_path = value

    @property
    def layout(self) -> LayoutMode:
        """LayoutMode: Layout mode."""
        return self._layout

    @layout.setter
    def layout(self, value: LayoutMode) -> None:
        self._layout = value

    @property
    def hist_file(self) -> Path:
        """:class:`pathlib.Path`: History file."""
        if sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            base_dir = os.getenv("XDG_DATA_HOME", "~/.local/share")
            hist_dir = Path("%s/s3fm" % base_dir).expanduser()
        else:
            # TODO: get windows config
            base_dir = os.getenv("APPDATA")
            hist_dir = Path("%s\\s3fm\\history" % base_dir).expanduser()
        if not hist_dir.exists():
            hist_dir.mkdir(parents=True)
        return hist_dir.joinpath("history.json")
