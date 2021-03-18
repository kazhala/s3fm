"""Module contains the file object and helper methods."""
from s3fm.id import ID


class File:
    """Used to store basic file information.

    Mainly used by :class:`~s3fm.ui.filepane.FilePane` to display
    them.

    It is also useful for custom :class:`~s3fm.api.config.LineModeConfig`
    as the user can leverage the information stored in this class.

    Args:
        name: Name of the file.
        type (ID): FileType id.
        info: Additional file information.
        hidden: Hidden file.
        index: Original file index
    """

    def __init__(
        self, name: str, type: ID, info: str, hidden: bool, index: int
    ) -> None:
        self._name = name
        self._type = type
        self._info = info
        self._hidden = hidden
        self._index = index

    @property
    def name(self) -> str:
        """str: Name of the file."""
        return self._name

    @property
    def type(self) -> ID:
        """ID: FileType id."""
        return self._type

    @property
    def info(self) -> str:
        """str: File information."""
        return self._info

    @property
    def hidden(self) -> bool:
        """bool: Is hidden file."""
        return self._hidden

    @property
    def index(self) -> int:
        """int: Original file index."""
        return self._index
