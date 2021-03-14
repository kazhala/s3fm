"""Module contains the modified :class:`prompt_toolkit.key_binding.KeyBindings` class."""
import asyncio
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys

from s3fm.id import ID, KB_MAPS, Direction, KBMode, LayoutMode

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
        "scroll_down": [{"keys": "j"}],
        "scroll_up": [{"keys": "k"}],
        "scroll_page_down": [{"keys": "c-d"}],
        "scroll_page_up": [{"keys": "c-u"}],
        "scroll_top": [
            {"keys": ["g", "g"]},
        ],
        "scroll_bottom": [{"keys": "G"}],
        "forward": [{"keys": "l"}, {"keys": Keys.Enter}],
        "backword": [{"keys": "h"}],
        "toggle_pane_hidden_files": [{"keys": ["z"]}],
    },
    KBMode.command: {"exit": [{"keys": "c-c"}, {"keys": "escape", "eager": True}]},
}


class KB(KeyBindings):
    """Modified :class:`prompt_toolkit.key_binding.KeyBindings` class to apply custom decorator logic.

    Args:
        app: To be provided by :class:`~s3fm.app.App`.
            Used to interact and instruct actions on :class:`~s3fm.app.App`.
        kb_maps: The :attr:`s3fm.api.config.KBConfig.kb_maps` in config class.
        custom_kb_maps: The :attr:`s3fm.api.config.KBConfig.custom_kb_maps` in config class.
        custom_kb_lookup: The :attr:`s3fm.api.config.KBConfig.custom_kb_lookup` in config class.
    """

    def __init__(
        self,
        app: "App",
        kb_maps: Dict[ID, KB_MAPS] = None,
        custom_kb_maps: Dict[ID, KB_MAPS] = None,
        custom_kb_lookup: Dict[ID, Dict[str, Any]] = None,
    ) -> None:
        self._activated = False
        self._app = app
        self._action_multiplier = None
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
                "layout_vertical": {
                    "func": self._app.switch_layout,
                    "args": [LayoutMode.vertical],
                },
                "layout_horizontal": {
                    "func": self._app.switch_layout,
                    "args": [LayoutMode.horizontal],
                },
                "layout_single": {
                    "func": self._app.switch_layout,
                    "args": [LayoutMode.single],
                },
                "pane_swap_down": {"func": self._swap_pane, "args": [Direction.down]},
                "pane_swap_up": {"func": self._swap_pane, "args": [Direction.up]},
                "pane_swap_left": {"func": self._swap_pane, "args": [Direction.left]},
                "pane_swap_right": {"func": self._swap_pane, "args": [Direction.right]},
                "scroll_down": self._scroll_down,
                "scroll_up": self._scroll_up,
                "scroll_page_down": {"func": self._scroll_down, "args": [1, True]},
                "scroll_page_up": {"func": self._scroll_up, "args": [1, True]},
                "scroll_bottom": {"func": self._scroll_down, "args": [1, False, True]},
                "scroll_top": {"func": self._scroll_up, "args": [1, False, True]},
                "forward": self._forward,
                "backword": self._backword,
                "toggle_pane_hidden_files": self._app.toggle_pane_hidden_files,
                "set_action_multiplier": self._set_action_multiplier,
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

        for i in range(10):
            self._factory(
                action="set_action_multiplier",
                mode_id=KBMode.normal,
                custom=False,
                raw=True,
                keys=str(i),
            )

    def _create_bindings(self, mode: ID, custom: bool = False) -> None:
        """Create keybindings.

        Interal function to create all keybindings in `kb_maps` and `custom_kb_maps`.

        Args:
            mode (ID): Indicate which mode to create the kb.
            custom: Indicate if its custom kb.
        """
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
        raw: bool = False,
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        **kwargs,
    ) -> None:
        """Call `add` to create bindings.

        Internal factory function to create keybindings in a loop.

        Args:
            action: The action to apply keybinding.
            mode_id (ID): Which mode to bind this function.
            custom: Flag indicate if its custom function.
            raw: Use the raw `KeyPressEvent` as the argument.
            keys: List of keys to bind to the function.
            filter: Enable the keybinding only if filter condition is satisfied.
            eager: Force priority on this keybinding.
            **kwargs: Additional args to provide to the :meth:`prompt_toolkit.key_binding.KeyBindings.add`.
        """
        if not isinstance(keys, list):
            keys = [keys]
        target_lookup = self._kb_lookup if not custom else self._custom_kb_lookup
        key_action = target_lookup[mode_id][action]
        if not isinstance(key_action, dict):
            key_action = {"func": key_action}
        function_args = key_action.get("args", [])
        if custom:
            function_args = [self._app]

        @self.add(*keys, filter=filter, eager=eager, mode_id=mode_id, raw=raw, **kwargs)
        def _(event: KeyPressEvent) -> None:
            key_action["func"](*function_args if not raw else [event])

    def _set_action_multiplier(self, event: KeyPressEvent) -> None:
        key_num = event.key_sequence[0].key
        if not self._action_multiplier:
            self._action_multiplier = int(key_num)
        else:
            self._action_multiplier = int("%s%s" % (self._action_multiplier, key_num))

    def _forward(self) -> None:
        """Perform forward action on current file."""
        asyncio.create_task(
            self._app.current_filepane.forward(
                self._app.current_filepane.current_selection
            )
        )

    def _backword(self) -> None:
        """Perform backword action."""
        asyncio.create_task(self._app.current_filepane.backword())

    def _swap_pane(self, direction: ID) -> None:
        """Move current pane to bottom split.

        Args:
            direction (ID): Swap direction id.
        """
        if direction == Direction.down or direction == Direction.up:
            self._app.pane_swap(direction, layout_id=LayoutMode.horizontal)
        else:
            self._app.pane_swap(direction, layout_id=LayoutMode.vertical)

    def _scroll_down(
        self,
        value: int = 1,
        page: bool = False,
        bottom: bool = False,
    ) -> None:
        """Move focused pane highlighted line down.

        Reference:
            :meth:`~s3fm.ui.filepane.FilePane.scroll_down`
        """
        if self.action_multiplier:
            value = self.action_multiplier
        self._app.current_filepane.scroll_down(value=value, page=page, bottom=bottom)

    def _scroll_up(self, value: int = 1, page: bool = False, top: bool = False) -> None:
        """Move focused pane highlighted line up.

        Reference:
            :meth:`~s3fm.ui.filepane.FilePane.scroll_up`
        """
        if self.action_multiplier:
            value = self.action_multiplier
        self._app.current_filepane.scroll_up(value=value, page=page, top=top)

    def add(
        self,
        *keys: Union[Keys, str],
        filter: Condition = Condition(lambda: True),
        eager: bool = False,
        mode_id: ID = KBMode.normal,
        raw: bool = False,
        **kwargs,
    ) -> Callable[[KeyHandlerCallable], KeyHandlerCallable]:
        """Bind keys to functions.

        It runs some additional checks before running the `KeyHandlerCallable`.

        Warning:
            It is recommended to use :meth:`s3fm.api.config.KBConfig.map` to create
            keybindings. Use this function only if you are familiar with :doc:`prompt_toolkit:index`
            and would like to access the :class:`prompt_toolkit.key_binding.key_processor.KeyPressEvent` or
            leverage additional kwargs such as `record_in_macro`.

        Args:
            keys: Any number of keys to bind to the function.
            filter: Enable the keybinding only if filter condition is satisfied.
            eager: Force priority on this keybinding.
            mode_id (ID): Which mode to bind this function.
            raw: Internal use only. For number keybinding.
            **kwargs: Additional args to provide to the :meth:`prompt_toolkit.key_binding.KeyBindings.add`.

        Returns:
            Callable[[KeyHandlerCallable], KeyHandlerCallable]: A function decorator to be used to decorate the custom function.

        Examples:
            The following code demonstrate how to use this :meth:`KB.add` function to create keybindings. It
            binds the `c-q` to exit the application in command mode. Reference :meth:`~s3fm.api.config.AppConfig.use_effect`
            for more information.

            >>> from s3fm.api.config import Config
            >>> from s3fm.id import KBMode
            >>> config = Config()
            >>> @config.app.use_effect
            ... def _(app):
            ...     if not app.rendered:
            ...         @app.kb.add("c-q", KBMode.command)
            ...         def _(_):
            ...             app.exit()
        """
        super_dec = super().add(
            *keys, filter=filter & self._mode[mode_id], eager=eager, **kwargs
        )

        def decorator(func: KeyHandlerCallable) -> KeyHandlerCallable:
            @super_dec
            def executable(event) -> None:
                if not self._activated:
                    return
                func(event)
                if not raw:
                    self._action_multiplier = None

            return executable

        return decorator

    @property
    def activated(self) -> bool:
        """bool: Keybinding activated status."""
        return self._activated

    @activated.setter
    def activated(self, value: bool) -> None:
        self._activated = value

    @property
    def action_multiplier(self) -> Optional[int]:
        """Optional[int]: Multiplier to apply to next numbered action."""
        return self._action_multiplier

    @action_multiplier.setter
    def action_multiplier(self, value) -> None:
        self._action_multiplier = value
