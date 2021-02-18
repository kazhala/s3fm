"""Module contains the modified `KeyBindings` class."""
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys

from s3fm.base import KB_MAPS, MODE, KBMode, PaneFocus

if TYPE_CHECKING:
    from s3fm.app import App

default_key_maps: Dict[MODE, KB_MAPS] = {
    KBMode.normal: {
        "exit": [{"keys": "c-c"}, {"keys": "q"}],
        "focus_pane": [{"keys": Keys.Tab}],
        "focus_cmd": [{"keys": ":"}],
        "layout_vertical": [{"keys": ["c-w", "v"]}],
        "layout_horizontal": [{"keys": ["c-w", "s"]}],
    },
    KBMode.command: {"exit": [{"keys": "c-c"}, {"keys": "escape", "eager": True}]},
}


class KB(KeyBindings):
    """Modified `KeyBindings` class to apply custom decorator logic."""

    def __init__(
        self,
        app: "App",
        kb_maps: Dict[MODE, KB_MAPS] = None,
        custom_kb_maps: Dict[MODE, KB_MAPS] = None,
        custom_kb_lookup: Dict[MODE, Dict[str, Any]] = None,
    ) -> None:
        """Initialise `KeyBindings`."""
        self._activated = False
        self._app = app
        self._mode = {
            KBMode.normal: self._app.normal_mode,
            KBMode.command: self._app.command_mode,
        }
        self._kb_maps = kb_maps or {KBMode.normal: {}, KBMode.command: {}}
        self._kb_lookup = {
            KBMode.normal: {
                "exit": self._app.exit,
                "focus_pane": self._focus_other_pane,
                "focus_cmd": self._app.focus_cmd,
                "layout_vertical": self._app.layout_vertical,
                "layout_horizontal": self._app.layout_horizontal,
            },
            KBMode.command: {"exit": self._app.exit_cmd},
        }
        self._custom_kb_maps = custom_kb_maps or {
            KBMode.normal: {},
            KBMode.command: {},
        }
        self._custom_kb_lookup = custom_kb_lookup or {
            KBMode.normal: {},
            KBMode.command: {},
        }
        super().__init__()

        self._create_bindings(KBMode.normal, custom=False)
        self._create_bindings(KBMode.command, custom=False)
        self._create_bindings(KBMode.normal, custom=True)
        self._create_bindings(KBMode.command, custom=True)

    def _create_bindings(self, mode, custom: bool = False) -> None:
        """Create keybindings."""
        target_maps = self._kb_maps if not custom else self._custom_kb_maps
        for action, binds in target_maps[mode].items():
            for bind in binds:
                self._factory(action=action, mode=mode, custom=custom, **bind)

    def _factory(
        self,
        action: str,
        mode: MODE,
        custom: bool,
        keys: Union[List[Union[Keys, str]], Union[Keys, str]],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        **kwargs,
    ) -> None:
        """Call `add` to create bindings."""
        if not isinstance(keys, list):
            keys = [keys]
        target_lookup = self._kb_lookup if not custom else self._custom_kb_lookup

        @self.add(*keys, filter=filter, eager=eager, mode=mode, **kwargs)
        def _(event: KeyPressEvent) -> None:
            target_lookup[mode][action](*[] if not custom else [self._app])

    def _focus_other_pane(self) -> None:
        """Focus the other file pane."""
        self._app.focus_pane(
            PaneFocus.left
            if self._app.current_focus == PaneFocus.right
            else PaneFocus.right
        )

    def add(
        self,
        *keys: Union[Keys, str],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        mode: MODE = KBMode.normal,
        **kwargs,
    ) -> Callable[[KeyHandlerCallable], KeyHandlerCallable]:
        """Run checks before running `KeyHandlerCallable`."""
        super_dec = super().add(
            *keys, filter=filter & self._mode[mode], eager=eager, **kwargs
        )

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
