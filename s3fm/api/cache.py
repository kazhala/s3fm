"""Module contains the utils to obtain and process cache result."""
from pathlib import Path

from s3fm.base import ID, Pane, PaneMode


class Cache:
    """Cache object which handles storing and reading cache."""

    def __init__(self) -> None:
        """Initialise states."""
        self._left_mode = PaneMode.s3
        self._left_path = ""
        self._right_mode = PaneMode.fs
        self._right_path = str(Path.cwd())
        self._focus = Pane.left

    async def read_cache(self) -> None:
        """Read cache."""
        self._left_mode = PaneMode.s3
        self._right_mode = PaneMode.fs
        self._focus = Pane.left

    @property
    def focus(self) -> int:
        """Get current focus id."""
        return self._focus

    @property
    def left_mode(self) -> ID:
        """Get left fs_mode."""
        return self._left_mode

    @property
    def right_mode(self) -> ID:
        """Get right fs_mode."""
        return self._right_mode
