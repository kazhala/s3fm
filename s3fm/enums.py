"""Module contains Enums that will be used as resource arguments."""
from enum import IntEnum


class KBMode(IntEnum):
    """Keybinding modes."""

    normal = 0
    command = 1


class PaneMode(IntEnum):
    """Pane operating modes."""

    s3 = 0
    fs = 1


class Pane(IntEnum):
    """Panes."""

    left = 0
    right = 1
    cmd = 2


class LayoutMode(IntEnum):
    """Layout modes."""

    vertical = 0
    horizontal = 1
    single = 2


class Direction(IntEnum):
    """Directions."""

    up = 0
    down = 1
    left = 2
    right = 3


class FileType(IntEnum):
    """File types."""

    bucket = 0
    dir = 1
    file = 2
    link = 3
    dir_link = 4
    exe = 5
