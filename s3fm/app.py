"""Module contains the main App class which creates the main application."""
import asyncio
from typing import Dict, Union

from prompt_toolkit.application import Application
from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, VSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Frame

from s3fm.api.cache import Cache
from s3fm.api.config import Config
from s3fm.api.kb import KB
from s3fm.base import ID, Direction, LayoutMode, Pane
from s3fm.exceptions import Bug
from s3fm.ui.commandpane import CommandPane
from s3fm.ui.filepane import FilePane
from s3fm.ui.optionpane import OptionPane
from s3fm.utils import kill_child_processes


class App:
    """Main app class which process the config and holds the top level layout."""

    def __init__(self, config: Config = None, no_cache: bool = False) -> None:
        """Process config, options and then create the application."""
        config = config or Config()

        self._style = Style.from_dict(dict(config.style))
        self._rendered = False
        self._no_cache = no_cache
        self._command_focus = False
        self._layout_mode = LayoutMode.vertical
        self._border = config.app.border
        self._current_focus = Pane.left

        self._command_mode = Condition(lambda: self._command_focus)
        self._normal_mode = Condition(lambda: not self._command_focus)
        self._layout_single = Condition(lambda: self._layout_mode == LayoutMode.single)

        self._left_pane = FilePane(
            pane_id=Pane.left,
            spinner_config=config.spinner,
            redraw=self._redraw,
            dimmension_offset=0 if not config.app.border else 2,
            layout_single=self._layout_single,
            focus=lambda: self._current_focus,
        )
        self._right_pane = FilePane(
            pane_id=Pane.right,
            spinner_config=config.spinner,
            redraw=self._redraw,
            dimmension_offset=0 if not config.app.border else 2,
            layout_single=self._layout_single,
            focus=lambda: self._current_focus,
        )
        self._command_pane = CommandPane()
        self._option_pane = OptionPane()

        self._kb = KB(
            app=self,
            kb_maps=config.kb.kb_maps,
            custom_kb_maps=config.kb.custom_kb_maps,
            custom_kb_lookup=config.kb.custom_kb_lookup,
        )

        self._app = Application(
            layout=self.layout,
            full_screen=True,
            after_render=self._after_render,
            style=self._style,
            key_bindings=self._kb,
        )

    def _redraw(self) -> None:
        """Instruct the app to redraw itself to the terminal."""
        self._app.invalidate()

    async def _load_pane_data(self, pane: FilePane, mode_id: ID) -> None:
        """Load the data for the specified pane and refersh the app.

        :param pane: a FilePane instance to load data
        :type pane: FilePane
        :param fs_mode: notify the FilePane whether to load data from s3 or local
        :type fs_mode: bool
        """
        await pane.load_data(mode_id=mode_id)
        self._redraw()

    async def _render_task(self) -> None:
        """Read cache and instruct left/right pane to load appropriate data."""
        cache = Cache()
        if not self._no_cache:
            await cache.read_cache()
        self.focus_pane(cache.focus)
        self._kb.activated = True
        await asyncio.gather(
            self._load_pane_data(pane=self._left_pane, mode_id=cache.left_mode),
            self._load_pane_data(pane=self._right_pane, mode_id=cache.right_mode),
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

    def focus_pane(self, pane_id: ID) -> None:
        """Focus specified pane and set the focus state.

        :param pane_id: the id of the pane to focus
            reference `self._pane_map`
        :type pane_id: FOCUS
        """
        self._current_focus = pane_id
        self._app.layout.focus(self.current_focus)

    def focus_other_pane(self) -> None:
        """Focus the other file pane."""
        if not self._layout_single():
            self.focus_pane(
                Pane.left if self._current_focus == Pane.right else Pane.right
            )

    def focus_cmd(self) -> None:
        """Focus the cmd pane."""
        self._app.layout.focus(self.panes[Pane.cmd])
        self._command_focus = True

    def exit_cmd(self) -> None:
        """Exit the command pane."""
        self.focus_pane(self._current_focus)
        self._command_focus = False

    def exit(self) -> None:
        """Exit the application and kill all spawed processes."""
        kill_child_processes()
        self._app.exit()

    def switch_layout(self, layout_id: ID) -> None:
        """Switch layout."""
        self._layout_mode = layout_id
        if layout_id != LayoutMode.single:
            self._app.layout = self.layout
            self.focus_pane(self._current_focus)

    def pane_swap(self, direction_id: ID, layout_id: ID) -> None:
        """Swap pane/layout."""
        if self._layout_single():
            return
        if (
            self._current_focus == Pane.right
            and (direction_id == Direction.right or direction_id == Direction.down)
            and self._layout_mode == layout_id
        ):
            return
        if (
            self._current_focus == Pane.left
            and (direction_id == Direction.left or direction_id == Direction.up)
            and self._layout_mode == layout_id
        ):
            return
        pane_swapped = False
        if not (
            self._current_focus == Pane.right
            and (direction_id == Direction.right or direction_id == Direction.down)
            and self._layout_mode != layout_id
        ) and not (
            self._current_focus == Pane.left
            and (direction_id == Direction.left or direction_id == Direction.up)
            and self._layout_mode != layout_id
        ):
            pane_swapped = True
            self._left_pane, self._right_pane = self._right_pane, self._left_pane
            self._left_pane.id, self._right_pane.id = (
                self._right_pane.id,
                self._left_pane.id,
            )
        self._layout_mode = layout_id
        self._app.layout = self.layout
        if pane_swapped:
            self.focus_other_pane()
        else:
            self.focus_pane(self._current_focus)

    @property
    def command_mode(self) -> Condition:
        """Get command mode condition."""
        return self._command_mode

    @property
    def normal_mode(self) -> Condition:
        """Get normal mode condition."""
        return self._normal_mode

    @property
    def current_focus(self) -> FilePane:
        """Get current app focus."""
        return self.filepanes[self._current_focus]

    @property
    def filepanes(self) -> Dict[ID, Union[FilePane]]:
        """Get only filepanes mappings."""
        return {
            Pane.left: self._left_pane,
            Pane.right: self._right_pane,
        }

    @property
    def panes(self) -> Dict[ID, Union[FilePane, CommandPane]]:
        """Get pane mappings."""
        return {
            Pane.left: self._left_pane,
            Pane.right: self._right_pane,
            Pane.cmd: self._command_pane,
        }

    @property
    def layout(self) -> Layout:
        """Get the app layout."""
        if self._layout_mode == LayoutMode.vertical:
            layout = HSplit(
                [VSplit([self._left_pane, self._right_pane]), self._command_pane]
            )

        elif self._layout_mode == LayoutMode.horizontal:
            layout = HSplit([self._left_pane, self._right_pane, self._command_pane])
        else:
            raise Bug("unexpected layout mode.")
        if self._border:
            layout = Frame(layout)
        return Layout(
            FloatContainer(
                content=layout,
                floats=[Float(content=self._option_pane)],
            )
        )
