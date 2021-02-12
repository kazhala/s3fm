"""Module contains the modified `KeyBindings` class."""
from typing import Callable, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.keys import Keys

from s3fm.base import KBMode

__all__ = ["COMMAND_MODE", "NORMAL_MODE", "KB"]


COMMAND_MODE = KBMode.command
NORMAL_MODE = KBMode.normal


class KB(KeyBindings):
    """Modified `KeyBindings` class to apply custom decorator logic."""

    def __init__(self, normal_mode: Condition, command_mode: Condition) -> None:
        """Initialise `KeyBindings`."""
        self._activated = False
        self._mode = {NORMAL_MODE: normal_mode, COMMAND_MODE: command_mode}
        self._command_mode = command_mode
        self._normal_mode = normal_mode
        self._kb_maps = {
            NORMAL_MODE: {"exit": [{"key": "c-c"}, {"key": "q"}]},
            COMMAND_MODE: {"exit": [{"key": "c-c"}, {"key": "escape", "eager": True}]},
        }
        super().__init__()

    def add(
        self,
        *keys: Union[Keys, str],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        mode: int = NORMAL_MODE
    ) -> Callable[[KeyHandlerCallable], KeyHandlerCallable]:
        """Run checks before running `KeyHandlerCallable`."""
        super_dec = super().add(*keys, filter=filter & self._mode[mode], eager=eager)

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
