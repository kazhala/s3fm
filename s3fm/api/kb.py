"""Module contains the modified `KeyBindings` class."""
from typing import Callable, Union

from prompt_toolkit.filters.base import FilterOrBool
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.keys import Keys


class KB(KeyBindings):
    """Modified `KeyBindings` class to apply custom decorator logic."""

    def __init__(self) -> None:
        """Initialise `KeyBindings`."""
        self._activated = False
        super().__init__()

    def add(
        self,
        *keys: Union[Keys, str],
        filter: FilterOrBool = True,
        eager: FilterOrBool = False,
    ) -> Callable[[KeyHandlerCallable], KeyHandlerCallable]:
        """Run checks before running `KeyHandlerCallable`."""
        super_dec = super().add(*keys, filter=filter, eager=eager)

        def decorator(func: KeyHandlerCallable) -> KeyHandlerCallable:
            @super_dec
            def executable(event) -> None:
                if not self._activated:
                    return
                func(event)

            return executable

        return decorator

    @property
    def activated(self) -> bool:
        """Get activated status."""
        return self._activated

    @activated.setter
    def activated(self, value: bool) -> None:
        """Set activated status."""
        self._activated = value
