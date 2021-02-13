"""Module contains the main App class which creates the main application."""
import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, VSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Frame

from s3fm.api.cache import Cache
from s3fm.api.config import Config
from s3fm.api.kb import KB
from s3fm.base import FOCUS, MODE, KBMode, PaneFocus
from s3fm.ui.commandpane import CommandPane
from s3fm.ui.filepane import FilePane
from s3fm.ui.optionpane import OptionPane
from s3fm.utils import kill_child_processes


class App:
    """Main app class which process the config and holds the top level layout."""

    def __init__(self, config: Config, no_cache: bool = False) -> None:
        """Process config, options and then create the application."""
        self._style = Style.from_dict(dict(config.style))
        self._rendered = False
        self._no_cache = no_cache
        self._left_pane = FilePane(
            pane_id=PaneFocus.left, spinner_config=config.spinner, redraw=self._redraw
        )
        self._right_pane = FilePane(
            pane_id=PaneFocus.right, spinner_config=config.spinner, redraw=self._redraw
        )
        self._command_pane = CommandPane()
        self._option_pane = OptionPane()
        self._command_focus = False

        window = HSplit(
            [VSplit([self._left_pane, self._right_pane]), self._command_pane]
        )
        if config.app.border:
            window = Frame(window)
        self._layout = Layout(
            FloatContainer(
                content=window,
                floats=[Float(content=self._option_pane)],
            )
        )

        self._pane_map = {
            PaneFocus.left: self._left_pane,
            PaneFocus.right: self._right_pane,
            PaneFocus.cmd: self._command_pane,
        }
        self._current_focus = PaneFocus.left
        self._layout.focus(self._pane_map[self._current_focus])

        self._command_mode = Condition(lambda: self._command_focus)
        self._normal_mode = Condition(lambda: not self._command_focus)
        self._kb = KB(self._normal_mode, self._command_mode)

        for kb_action, kb_binds in self._kb.list_kbs(KBMode.normal):
            for bind in kb_binds:
                self._kb.factory(
                    action=getattr(self, kb_action), mode=KBMode.normal, **bind
                )

        for kb_action, kb_binds in self._kb.list_kbs(KBMode.command):
            for bind in kb_binds:
                self._kb.factory(
                    action=getattr(self, kb_action), mode=KBMode.command, **bind
                )

        self._app = Application(
            layout=self._layout,
            full_screen=True,
            after_render=self._after_render,
            style=self._style,
            key_bindings=self._kb,
        )

    def _kb_norm_exit(self, event: KeyPressEvent) -> None:
        """Exit the application in normal mode."""
        kill_child_processes()
        event.app.exit()

    def _kb_norm_focus_pane(self, event: KeyPressEvent) -> None:
        """Focus next file pane in normal mode."""
        self._focus_pane(
            PaneFocus.left
            if self._current_focus == PaneFocus.right
            else PaneFocus.right
        )

    def _kb_norm_focus_cmd(self, event: KeyPressEvent) -> None:
        """Focus cmd pane in normal mode."""
        self._layout.focus(self._pane_map[PaneFocus.cmd])
        self._command_focus = True

    def _kb_cmd_exit(self, event: KeyPressEvent) -> None:
        """Focus file pane in command mode."""
        self._focus_pane(self._current_focus)
        self._command_focus = False

    def _redraw(self) -> None:
        """Instruct the app to redraw itself to the terminal."""
        self._app.invalidate()

    def _focus_pane(self, pane: FOCUS) -> None:
        """Focus specified pane and set the focus state.

        :param pane_id: the id of the pane to focus
            reference `self._pane_map`
        :type pane_id: FOCUS
        """
        self._current_focus = pane
        self._layout.focus(self._pane_map[self._current_focus])

    async def _load_pane_data(self, pane: FilePane, mode: MODE) -> None:
        """Load the data for the specified pane and refersh the app.

        :param pane: a FilePane instance to load data
        :type pane: FilePane
        :param fs_mode: notify the FilePane whether to load data from s3 or local
        :type fs_mode: bool
        """
        await pane.load_data(mode=mode)
        self._redraw()

    async def _render_task(self) -> None:
        """Read cache and instruct left/right pane to load appropriate data."""
        cache = Cache()
        if not self._no_cache:
            await cache.read_cache()
        self._focus_pane(cache.focus)
        self._kb.activated = True
        await asyncio.gather(
            self._load_pane_data(pane=self._left_pane, mode=cache.left_mode),
            self._load_pane_data(pane=self._right_pane, mode=cache.right_mode),
        )

    def _after_render(self, app) -> None:
        """Run after the app is running, same as `useEffect` in react.js."""
        if not self._rendered:
            self._rendered = True
            asyncio.create_task(self._left_pane.spinner.spin())
            asyncio.create_task(self._right_pane.spinner.spin())
            asyncio.create_task(self._render_task())

    async def run(self) -> None:
        """Run the application in async mode."""
        await self._app.run_async()
