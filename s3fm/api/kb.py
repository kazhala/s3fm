"""Module contains the modified :class:`prompt_toolkit.key_binding.KeyBindings` class."""
import inspect
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyHandlerCallable
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys

from s3fm.enums import Direction, KBMode, LayoutMode

if TYPE_CHECKING:
    from s3fm.app import App

KBs = Union[Keys, str]
KB_MAPS = Dict[str, List[Dict[str, Union[bool, KBs, Condition, List[KBs]]]]]


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
        kb_maps: Dict[KBMode, KB_MAPS] = None,
        custom_kb_maps: Dict[KBMode, KB_MAPS] = None,
        custom_kb_lookup: Dict[KBMode, Dict[str, Any]] = None,
    ) -> None:
        self._activated = False
        self._app = app
        self._action_multiplier = None
        self._mode = {
            KBMode.normal: self._app.normal_mode,
            KBMode.command: self._app.command_mode,
            KBMode.error: self._app.error_mode,
        }
        self._kb_maps = kb_maps or {
            KBMode.normal: {},
            KBMode.command: {},
            KBMode.error: {},
            KBMode.search: {},
        }
        self._kb_lookup = {
            KBMode.normal: {
                "exit": self._app.exit,
                "layout_vertical": {
                    "func": self._app.layout_switch,
                    "args": [LayoutMode.vertical],
                },
                "layout_horizontal": {
                    "func": self._app.layout_switch,
                    "args": [LayoutMode.horizontal],
                },
                "layout_single": {
                    "func": self._app.layout_switch,
                    "args": [LayoutMode.single],
                },
                "cmd_focus": self._app.cmd_focus,
                "pane_focus": self._app.pane_focus_other,
                "pane_swap_down": {"func": self._swap_pane, "args": [Direction.down]},
                "pane_swap_up": {"func": self._swap_pane, "args": [Direction.up]},
                "pane_swap_left": {"func": self._swap_pane, "args": [Direction.left]},
                "pane_swap_right": {"func": self._swap_pane, "args": [Direction.right]},
                "pane_scroll_down": self._pane_scroll_down,
                "pane_scroll_up": self._pane_scroll_up,
                "pane_scroll_down_page": {
                    "func": self._pane_scroll_down,
                    "args": [1, True],
                },
                "pane_scroll_up_page": {
                    "func": self._pane_scroll_up,
                    "args": [1, True],
                },
                "pane_scroll_bottom": {
                    "func": self._pane_scroll_down,
                    "args": [1, False, True],
                },
                "pane_scroll_top": {
                    "func": self._pane_scroll_up,
                    "args": [1, False, True],
                },
                "pane_page_up": self._pane_page_up,
                "pane_page_down": self._pane_page_down,
                "pane_forward": self._pane_forward,
                "pane_backword": self._pane_backword,
                "pane_toggle_hidden_files": self._app.pane_toggle_hidden_files,
                "pane_set_action_multiplier": self._pane_set_action_multiplier,
                "pane_switch_mode": self._app.pane_switch_mode,
            },
            KBMode.command: {"exit": self._app.cmd_exit},
            KBMode.error: {"exit": self._app.set_error},
            KBMode.search: {},
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

        self._create_bindings(KBMode.error, custom=False)
        self._create_bindings(KBMode.normal, custom=False)
        self._create_bindings(KBMode.command, custom=False)
        self._create_bindings(KBMode.normal, custom=True)
        self._create_bindings(KBMode.command, custom=True)
        self._create_bindings(KBMode.search, custom=False)

        for i in range(10):
            self._factory(
                action="pane_set_action_multiplier",
                mode=KBMode.normal,
                custom=False,
                raw=True,
                keys=str(i),
            )

    def _create_bindings(self, mode: KBMode, custom: bool = False) -> None:
        """Create keybindings.

        Interal function to create all keybindings in `kb_maps` and `custom_kb_maps`.

        Args:
            mode: Indicate which mode to create the kb.
            custom: Indicate if its custom kb.
        """
        target_maps = self._kb_maps if not custom else self._custom_kb_maps
        for action, binds in target_maps[mode].items():
            for bind in binds:
                self._factory(action=action, mode=mode, custom=custom, **bind)  # type: ignore

    def _factory(
        self,
        action: str,
        mode: KBMode,
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
            mode: Which mode to bind this function.
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
        key_action = target_lookup[mode][action]
        if not isinstance(key_action, dict):
            key_action = {"func": key_action}
        function_args = key_action.get("args", [])
        if custom:
            function_args = [self._app]

        @self.add(*keys, filter=filter, eager=eager, mode=mode, raw=raw, **kwargs)
        async def _(event: KeyPressEvent) -> None:
            if inspect.iscoroutinefunction(key_action["func"]):
                await key_action["func"](*function_args if not raw else [event])
            else:
                key_action["func"](*function_args if not raw else [event])

    def _pane_set_action_multiplier(self, event: KeyPressEvent) -> None:
        key_num = event.key_sequence[0].key
        if not self._action_multiplier:
            self._action_multiplier = int(key_num)
        else:
            self._action_multiplier = int("%s%s" % (self._action_multiplier, key_num))

    def _pane_page_up(self) -> None:
        """Scroll page up."""
        self._app.current_filepane.page_up()

    def _pane_page_down(self) -> None:
        """Scroll page down."""
        self._app.current_filepane.page_down()

    async def _pane_forward(self) -> None:
        """Perform forward action on current file."""
        await self._app.current_filepane.forward()

    async def _pane_backword(self) -> None:
        """Perform backword action."""
        await self._app.current_filepane.backword()

    def _swap_pane(self, direction: Direction) -> None:
        """Move current pane to bottom split.

        Args:
            direction: Swap direction.
        """
        if direction == Direction.down or direction == Direction.up:
            self._app.pane_swap(direction, layout=LayoutMode.horizontal)
        else:
            self._app.pane_swap(direction, layout=LayoutMode.vertical)

    def _pane_scroll_down(
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

    def _pane_scroll_up(
        self, value: int = 1, page: bool = False, top: bool = False
    ) -> None:
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
        mode: KBMode = KBMode.normal,
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
            mode: Which mode to bind this function.
            raw: Internal use only. For number keybinding.
            **kwargs: Additional args to provide to the :meth:`prompt_toolkit.key_binding.KeyBindings.add`.

        Returns:
            Callable[[KeyHandlerCallable], KeyHandlerCallable]: A function decorator to be used to decorate the custom function.

        Examples:
            The following code demonstrate how to use this :meth:`KB.add` function to create keybindings. It
            binds the `c-q` to exit the application in command mode. Reference :meth:`~s3fm.api.config.AppConfig.use_effect`
            for more information.

            >>> from s3fm.api.config import Config
            >>> from s3fm.enums import KBMode
            >>> config = Config()
            >>> @config.app.use_effect
            ... def _(app):
            ...     if not app.rendered:
            ...         @app.kb.add("c-q", KBMode.command)
            ...         def _(_):
            ...             app.exit()
        """
        super_dec = super().add(
            *keys, filter=filter & self._mode[mode], eager=eager, **kwargs
        )

        def decorator(func: KeyHandlerCallable) -> KeyHandlerCallable:
            @super_dec
            async def executable(event) -> None:
                if not self._activated:
                    return
                if inspect.iscoroutinefunction(func):
                    await func(event)  # type: ignore
                else:
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
