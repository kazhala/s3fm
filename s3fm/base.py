"""Module contains base classes and IDs.

ID is an identifier that can be used to find certain resource
in some of the mappings. More information about ID please reference
:ref:`pages/configuration:ID`.
"""
from typing import Any, Dict, Iterator, List, NamedTuple, Tuple, Union

from prompt_toolkit.filters.base import Condition, FilterOrBool
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import AnyContainer, ConditionalContainer

from s3fm.ui.spinner import Spinner

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
File = NamedTuple(
    "File",
    [("name", str), ("type", ID), ("info", str), ("hidden", bool), ("index", int)],
)


class BaseStyleConfig:
    """Base style config class.

    Inherit this class to create complex style options
    such as :class:`~s3fm.api.config.StyleConfig`.

    The `__iter__` method will help transform this class into
    a processable dictionary for :meth:`prompt_toolkit.styles.Style.from_dict`.
    """

    def clear(self) -> None:
        """Clear all default styles recursively.

        This will completly wipe all the default style value.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, BaseStyleConfig):
                value.clear()
            else:
                setattr(self, key, "")

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """Customise the iteration method for custom :func:`dict` behavior.

        When calling :func:`dict` on this class, nested :class:`BaseStyleConfig`
        will return as attribute as chained string as the key.

        Yields:
            Yields a tuple of key and value.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, BaseStyleConfig):
                for subkey, subvalue in value.__dict__.items():
                    yield ("%s.%s" % (key, subkey), subvalue)
            else:
                yield (key, value)


class BasePane(ConditionalContainer):
    """Base class to create a pane in the app.

    Internal use only, this is mainly a work around for type checker
    type hinting and error screaming.
    """

    spinner: Spinner

    def __init__(self, content: AnyContainer, filter: FilterOrBool) -> None:
        super().__init__(content=content, filter=filter)

    def handle_down(self):
        """Handle down movement."""
        pass

    def handle_up(self):
        """Handle up movement."""
        pass

    def handle_left(self):
        """Handle left movement."""
        pass

    def handle_right(self):
        """Handle right movement."""
        pass

    async def filter_files(self):
        """Hanlde additional logic during movement."""
        pass

    @property
    def display_hidden_files(self):
        """Get hidden file display status."""
        pass

    @display_hidden_files.setter
    def display_hidden_files(self, value: bool = None):
        """Change hidden file display status.

        Args:
            value: The value to set to hidden file display status.
        """
        pass
