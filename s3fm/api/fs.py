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
        path = path or ""
        self._path = Path(path).expanduser()

    async def get_paths(self) -> List[File]:
        """Async wrapper to retrieve all paths/files under `self._path`."""

        def _get_filetype(path: Path) -> ID:
            if path.is_dir():
                return FileType.dir if not path.is_symlink() else FileType.dir_link
            else:
                if path.is_symlink():
                    return FileType.link
                if os.access(path, os.X_OK):
                    return FileType.exe
                return FileType.file

        with ProcessPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, self.list_files)
            response = []
            if str(self._path) != "/":
                response.append(
                    File(name="..", type=FileType.dir, hidden=False, index=0, info="")
                )
            for index, path in enumerate(result):
                file_type = _get_filetype(path)
                name = str(path.name)
                response.append(
                    File(
                        name="%s%s"
                        % (
                            name,
                            "/"
                            if file_type == FileType.dir
                            or file_type == FileType.dir_link
                            else "",
                        ),
                        type=file_type,
                        info="h",
                        hidden=name.startswith("."),
                        index=index + 1 if str(self._path) != "/" else index,
                    )
                )
            return response

    def list_files(self) -> List[Path]:
        """Retrieve all files/paths under `self._path`."""
        return list(
            sorted(self._path.iterdir(), key=lambda file: (file.is_file(), file.name))
        )

    @property
    def path(self) -> Path:
        """Get current path."""
        return self._path
