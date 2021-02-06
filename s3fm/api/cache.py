"""Module contains the utils to obtain and process cache result."""
from pathlib import Path


class Cache:
    """Cache object which handles storing and reading cache."""

    def __init__(self) -> None:
        """Initialise states."""
        self._left_fs_mode = False
        self._left_path = ""
        self._right_fs_mode = True
        self._right_path = str(Path.cwd())
        self._focus = 0

    async def read_cache(self) -> None:
        """Read cache."""
        self._left_fs_mode = False
        self._right_fs_mode = True
        self._focus = 0

    @property
    def focus(self) -> int:
        """Get current focus id."""
        return self._focus

    @property
    def left_fs_mode(self) -> bool:
        """Get left fs_mode."""
        return self._left_fs_mode

    @property
    def right_fs_mode(self) -> bool:
        """Get right fs_mode."""
        return self._right_fs_mode
