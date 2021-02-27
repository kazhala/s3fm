"""Module contains the modified `KeyBindings` class."""
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys

from s3fm.base import ID, KB_MAPS, Direction, KBMode, LayoutMode

if TYPE_CHECKING:
    from s3fm.app import App

default_key_maps: Dict[ID, KB_MAPS] = {
    KBMode.normal: {
        "exit": [{"keys": "c-c"}, {"keys": "q"}],
        "focus_pane": [{"keys": Keys.Tab}],
        "focus_cmd": [{"keys": ":"}],
        "layout_vertical": [{"keys": ["c-w", "v"]}],
        "layout_horizontal": [{"keys": ["c-w", "s"]}],
        "layout_single": [{"keys": ["c-w", "o"]}],
        "pane_swap_down": [{"keys": ["c-w", "J"]}],
        "pane_swap_up": [{"keys": ["c-w", "K"]}],
        "pane_swap_left": [{"keys": ["c-w", "H"]}],
        "pane_swap_right": [{"keys": ["c-w", "L"]}],
        "handle_down": [{"keys": "j"}],
        "handle_up": [{"keys": "k"}],
        "toggle_pane_hidden_files": [{"keys": ["z"]}],
    },
    KBMode.command: {"exit": [{"keys": "c-c"}, {"keys": "escape", "eager": True}]},
}


class KB(KeyBindings):
    """Modified `KeyBindings` class to apply custom decorator logic."""

    def __init__(
        self,
        app: "App",
        kb_maps: Dict[ID, KB_MAPS] = None,
        custom_kb_maps: Dict[ID, KB_MAPS] = None,
        custom_kb_lookup: Dict[ID, Dict[str, Any]] = None,
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
                "focus_pane": self._app.focus_other_pane,
                "focus_cmd": self._app.focus_cmd,
                "layout_vertical": self._layout_vertical,
                "layout_horizontal": self._layout_horizontal,
                "layout_single": self._layout_single,
                "pane_swap_down": self._swap_pane_down,
                "pane_swap_up": self._swap_pane_up,
                "pane_swap_left": self._swap_pane_left,
                "pane_swap_right": self._swap_pane_right,
                "handle_down": self._handle_down,
                "handle_up": self._handle_up,
                "toggle_pane_hidden_files": self._app.toggle_pane_hidden_files,
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
                self._factory(action=action, mode_id=mode, custom=custom, **bind)

    def _factory(
        self,
        action: str,
        mode_id: ID,
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

        @self.add(*keys, filter=filter, eager=eager, mode_id=mode_id, **kwargs)
        def _(_: KeyPressEvent) -> None:
            target_lookup[mode_id][action](*[] if not custom else [self._app])

    def _swap_pane_down(self) -> None:
        """Move current pane to bottom split."""
        self._app.pane_swap(Direction.down, layout_id=LayoutMode.horizontal)

    def _swap_pane_up(self) -> None:
        """Move current pane to top split."""
        self._app.pane_swap(Direction.up, layout_id=LayoutMode.horizontal)

    def _swap_pane_left(self) -> None:
        """Move current pane to left split."""
        self._app.pane_swap(Direction.left, layout_id=LayoutMode.vertical)

    def _swap_pane_right(self) -> None:
        """Move current pane to right split."""
        self._app.pane_swap(Direction.right, layout_id=LayoutMode.vertical)

    def _layout_vertical(self) -> None:
        """Switch layout to vertical mode."""
        self._app.switch_layout(LayoutMode.vertical)

    def _layout_horizontal(self) -> None:
        """Switch layout to horizontal mode."""
        self._app.switch_layout(LayoutMode.horizontal)

    def _layout_single(self) -> None:
        """Switch layout to horizontal mode."""
        self._app.switch_layout(LayoutMode.single)

    def _handle_down(self) -> None:
        """Move focused pane highlighted line down."""
        self._app.current_focus.handle_down()

    def _handle_up(self) -> None:
        """Move focused pane highlighted line up."""
        self._app.current_focus.handle_up()

    def add(
        self,
        *keys: Union[Keys, str],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        mode_id: ID = KBMode.normal,
        **kwargs,
    ) -> Callable[[KeyHandlerCallable], KeyHandlerCallable]:
        """Run checks before running `KeyHandlerCallable`."""
        super_dec = super().add(
            *keys, filter=filter & self._mode[mode_id], eager=eager, **kwargs
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
