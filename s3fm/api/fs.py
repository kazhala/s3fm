"""Module contains the main api class to access file system."""
import asyncio
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List


class FS:
    """Class to access/interact local file system.

    :param path: local file directory
    :type path: str
    """

    def __init__(self, path: str = None) -> None:
        """Initialise the starting path."""
        self._path = path or ""

    async def get_paths(self) -> List[str]:
        """Async wrapper to retrieve all paths/files under `self._path`."""
        with ProcessPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, self.list_files)
            return result

    def list_files(self) -> List[str]:
        """Retrieve all files/paths under `self._path`."""
        return [str(path) for path in Path(self._path).iterdir()]
