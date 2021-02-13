"""Module contains the modified `KeyBindings` class."""
from typing import TYPE_CHECKING, Callable, Dict, List, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys

from s3fm.base import KB_MAPS, MODE, KBMode, PaneFocus

if TYPE_CHECKING:
    from s3fm.app import App

default_kb_maps: Dict[MODE, KB_MAPS] = {
    KBMode.normal: {
        "exit": [{"keys": "c-c"}, {"keys": "q"}],
        "focus_pane": [{"keys": Keys.Tab}],
        "focus_cmd": [{"keys": ":"}],
    },
    KBMode.command: {"exit": [{"keys": "c-c"}, {"keys": "escape", "eager": True}]},
}


class KB(KeyBindings):
    """Modified `KeyBindings` class to apply custom decorator logic."""

    def __init__(self, app: "App", kb_maps: Dict[MODE, KB_MAPS] = None) -> None:
        """Initialise `KeyBindings`."""
        self._activated = False
        self._app = app
        self._mode = {
            KBMode.normal: self._app.normal_mode,
            KBMode.command: self._app.command_mode,
        }
        self._kb_maps = kb_maps or default_kb_maps
        self._kb_lookup = {
            KBMode.normal: {
                "exit": [{"func": self._app.exit}],
                "focus_pane": [
                    {
                        "func": self._app.focus_pane,
                        "args": [
                            PaneFocus.left
                            if self._app.current_focus == PaneFocus.right
                            else PaneFocus.right
                        ],
                    }
                ],
                "focus_cmd": [{"func": self._app.focus_cmd}],
            },
            KBMode.command: {"exit": [{"func": self._app.exit_cmd}]},
        }
        super().__init__()

        def _factory(
            action: str,
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
                for method in self._kb_lookup[mode][action]:
                    method["func"](*method.get("args", []))

        for action, binds in self._kb_maps[KBMode.normal].items():
            for bind in binds:
                _factory(action, KBMode.normal, **bind)

        for action, binds in self._kb_maps[KBMode.command].items():
            for bind in binds:
                _factory(action, KBMode.normal, **bind)

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
