"""Module contains the main api class to access file system."""
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List

from s3fm.base import ID, File, FileType


class FS:
    """Class to access/interact local file system.

    :param path: local file directory
    :type path: str
    """

    def __init__(self, path: str = None) -> None:
        """Initialise the starting path."""
        self._path = path or ""

    async def get_paths(self) -> List[File]:
        """Async wrapper to retrieve all paths/files under `self._path`."""

        def _get_filetype(path: Path) -> ID:
            if path.is_dir():
                return FileType.dir if not path.is_symlink() else FileType.dir_link
            else:
                if os.access(path, os.X_OK):
                    return FileType.exe
                return FileType.file if not path.is_symlink() else FileType.link

        with ProcessPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, self.list_files)
            return [File(name=str(path), type=_get_filetype(path)) for path in result]

    def list_files(self) -> List[Path]:
        """Retrieve all files/paths under `self._path`."""
        return list(sorted(Path(self._path).iterdir(), key=lambda file: file.is_file()))

    @property
    def path(self) -> str:
        """Get current path."""
        return self._path or "/"
