"""Module contains the file object and helper methods."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

from s3fm.enums import FileType


@dataclass
class File:
    """Used to store basic file information.

    Mainly used by :class:`~s3fm.ui.filepane.FilePane` to display
    them.

    It is also useful for custom :class:`~s3fm.api.config.LineModeConfig`
    as the user can leverage the information stored in this class.

    Args:
        name: Name of the file.
        type: FileType.
        info: Additional file information.
        hidden: Hidden file.
        index: Original file index
        raw: Full path of the file.
    """

    name: str
    type: FileType
    info: str
    hidden: bool
    index: int
    raw: Optional[Union[Path, Dict[str, Any]]]
