"""Module contains the utils to obtain and process cache result."""
import asyncio
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

    async def _read_cache(self) -> None:
        """Read cache."""
        self._left_fs_mode = False
        self._right_fs_mode = True
        self._focus = 0
