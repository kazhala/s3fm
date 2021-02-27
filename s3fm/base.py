"""Module contains base classes and enums."""
from typing import Any, Dict, Iterator, List, NamedTuple, Tuple, Union

from prompt_toolkit.filters.base import Condition, FilterOrBool
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import AnyContainer, ConditionalContainer

ID = int
KBs = Union[Keys, str]
KB_MAPS = Dict[str, List[Dict[str, Union[bool, KBs, Condition, List[KBs]]]]]

KBMode = NamedTuple("KBMode", [("normal", ID), ("command", ID)])(0, 1)
PaneMode = NamedTuple("PaneMode", [("s3", ID), ("fs", ID)])(0, 1)
Pane = NamedTuple("PaneFocus", [("left", ID), ("right", ID), ("cmd", ID)])(0, 1, 2)
LayoutMode = NamedTuple(
    "LayoutMode", [("vertical", ID), ("horizontal", ID), ("single", ID)]
)(0, 1, 2)
Direction = NamedTuple(
    "LayoutMode", [("up", ID), ("down", ID), ("left", ID), ("right", ID)]
)(0, 1, 2, 3)

FileType = NamedTuple(
    "FileType",
    [
        ("bucket", ID),
        ("dir", ID),
        ("file", ID),
        ("link", ID),
        ("dir_link", ID),
        ("exe", ID),
    ],
)(0, 1, 2, 3, 4, 5)
File = NamedTuple("File", [("name", str), ("type", ID), ("info", str)])


class BaseStyleConfig:
    """Base style config class.

    Inherit this class to create complex style options
    such as `class:spinner.text`.
    """

    def clear(self) -> None:
        """Clear all default styles recursively."""
        for key, value in self.__dict__.items():
            if isinstance(value, BaseStyleConfig):
                value.clear()
            else:
                setattr(self, key, "")

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """Customise the iteration method for custom `dict` behavior.

        When calling `dict` on this class, nested `BaseStyleConfig`
        will return as attribute as chained string as the key.

        E.g `spinner.prefix`.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, BaseStyleConfig):
                for subkey, subvalue in value.__dict__.items():
                    yield ("%s.%s" % (key, subkey), subvalue)
            else:
                yield (key, value)


class BasePane(ConditionalContainer):
    """Base class to create a pane in the app."""

    def __init__(self, content: AnyContainer, filter: FilterOrBool) -> None:
        """Create the container."""
        super().__init__(content=content, filter=filter)

    def handle_down(self) -> None:
        """Handle down movement."""
        pass

    def handle_up(self) -> None:
        """Handle up movement."""
        pass

    def handle_left(self) -> None:
        """Handle left movement."""
        pass

    def handle_right(self) -> None:
        """Handle right movement."""
        pass
