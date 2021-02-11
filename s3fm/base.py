"""Module contains base classes and common typings."""
from typing import Any, Iterator, List, Tuple

FormattedText = List[Tuple[str, str]]


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
