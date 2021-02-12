"""Module contains base classes and enums."""
from typing import Any, Iterator, NamedTuple, Tuple

KBMode = NamedTuple("KBMode", [("normal", int), ("command", int)])(0, 1)
PaneMode = NamedTuple("PaneMode", [("s3", int), ("fs", int)])(0, 1)
PaneFocus = NamedTuple("PaneFocus", [("left", int), ("right", int), ("cmd", int)])(
    0, 1, 2
)

MODE = int
FOCUS = int


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