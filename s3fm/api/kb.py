"""Module contains the modified `KeyBindings` class."""
from typing import Any, Callable, Iterator, List, Tuple, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys

from s3fm.base import MODE, KBMode
from s3fm.exceptions import Bug


class KB(KeyBindings):
    """Modified `KeyBindings` class to apply custom decorator logic."""

    def __init__(self, normal_mode: Condition, command_mode: Condition) -> None:
        """Initialise `KeyBindings`."""
        self._activated = False
        self._mode = {KBMode.normal: normal_mode, KBMode.command: command_mode}
        self._command_mode = command_mode
        self._normal_mode = normal_mode
        self._kb_maps = {
            KBMode.normal: {
                "exit": [{"keys": "c-c"}, {"keys": "q"}],
                "focus_pane": [{"keys": Keys.Tab}],
                "focus_cmd": [{"keys": ":"}],
            },
            KBMode.command: {
                "exit": [{"keys": "c-c"}, {"keys": "escape", "eager": True}]
            },
        }
        super().__init__()

    def list_kbs(self, mode: MODE) -> Iterator[Tuple[str, Any]]:
        """List modified keybinding information."""
        if mode == KBMode.normal:
            for key, item in self._kb_maps[KBMode.normal].items():
                yield ("_kb_norm_%s" % key, item)
        elif mode == KBMode.command:
            for key, item in self._kb_maps[KBMode.command].items():
                yield ("_kb_cmd_%s" % key, item)
        else:
            raise Bug("unexpected kb mode")

    def factory(
        self,
        action: Callable[[KeyPressEvent], None],
        mode: MODE,
        keys: Union[List[Union[Keys, str]], Union[Keys, str]],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
    ) -> None:
        """Create keybindings."""
        if not isinstance(keys, list):
            keys = [keys]

        @self.add(*keys, filter=filter, eager=eager, mode=mode)
        def _(event: KeyPressEvent) -> None:
            action(event)

    def add(
        self,
        *keys: Union[Keys, str],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        mode: MODE = KBMode.normal
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
