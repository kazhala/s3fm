"""Module contains the api class to access/interact with the local file system."""
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional

from s3fm.exceptions import Bug
from s3fm.id import ID, File, FileType


class FS:
    """Class to access/interact local file system.

    Args:
        path: Local directory path as the default path.
    """

    def __init__(self, path: str = None) -> None:
        path = path or ""
        self._path = Path(path).expanduser()

    async def cd(
        self, path: Optional[Path] = None, override: bool = False
    ) -> List[File]:
        """Navigate into another directory.

        Args:
            path: A :class:`pathlib.Path` object to cd into.
                If not provided, navigate to current path parent.
            override: Change directory to a absolute new path without
                any consideration of the current path.

        Returns:
            A list of files in the new directory.

        Raises:
            Bug: when the supplied :class`pathlib.Path` object is not a directory.
        """
        if not path:
            self._path = self._path.parent
        else:
            if not path.is_dir:
                raise Bug("target path is not a directory.")
            if override:
                self._path = path
            else:
                self._path = self._path.joinpath(path)
        return await self.get_paths()

    async def get_paths(self) -> List[File]:
        """Async wrapper to retrieve all paths/files under :attr:`FS.path`.

        Retrieve a list of files under :obj:`concurrent.futures.ProcessPoolExecutor`.

        Returns:
            A list of :class:`~s3fm.id.File`.

        Examples:
            >>> import asyncio
            >>> from s3fm.api.fs import FS
            >>> async def main():
            ...     fs = FS()
            ...     files = await fs.get_paths()
            >>> asyncio.run(main())
        """

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
            result = await loop.run_in_executor(executor, self._list_files)
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

    def _list_files(self) -> List[Path]:
        """Retrieve all files/paths under :attr:`FS.path`."""
        return list(
            sorted(self._path.iterdir(), key=lambda file: (file.is_file(), file.name))
        )

    @property
    def path(self) -> Path:
        """:obj:`pathlib.Path`: Current path."""
        return self._path
