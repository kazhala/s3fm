"""Module contains base classes and enums."""
from typing import Any, Dict, Iterator, List, NamedTuple, Tuple, Union

from prompt_toolkit.filters.base import Condition, FilterOrBool
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import AnyContainer, ConditionalContainer

KBMode = NamedTuple("KBMode", [("normal", int), ("command", int)])(0, 1)
PaneMode = NamedTuple("PaneMode", [("s3", int), ("fs", int)])(0, 1)
Pane = NamedTuple("PaneFocus", [("left", int), ("right", int), ("cmd", int)])(0, 1, 2)
LayoutMode = NamedTuple(
    "LayoutMode", [("vertical", int), ("horizontal", int), ("single", int)]
)(0, 1, 2)
Direction = NamedTuple(
    "LayoutMode", [("up", int), ("down", int), ("left", int), ("right", int)]
)(0, 1, 2, 3)
ChoiceType = NamedTuple(
    "ChoiceType",
    [
        ("s3_bucket", int),
        ("s3_file", int),
        ("s3_dir", int),
        ("local_file", int),
        ("local_dir", int),
    ],
)(0, 1, 2, 3, 4)

ID = int
KBs = Union[Keys, str]
KB_MAPS = Dict[str, List[Dict[str, Union[bool, KBs, Condition, List[KBs]]]]]
CHOICES = Dict[str, Any]


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
