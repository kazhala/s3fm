"""Module contains Enums that will be used as resource arguments."""
from enum import Enum


class KBMode(Enum):
    """Keybinding modes."""

    normal = 0
    command = 1


class PaneMode(Enum):
    """Pane operating modes."""

    s3 = 0
    fs = 1


class Pane(Enum):
    """Panes."""

    left = 0
    right = 1
    cmd = 2


class LayoutMode(Enum):
    """Layout modes."""

    vertical = 0
    horizontal = 1
    single = 2


class Direction(Enum):
    """Directions."""

    up = 0
    down = 1
    left = 2
    right = 3


class FileType(Enum):
    """File types."""

    bucket = 0
    dir = 1
    file = 2
    link = 3
    dir_link = 4
    exe = 5
