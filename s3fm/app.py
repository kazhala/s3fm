"""Module contains the main App class which creates the main application.

User should not directly be using this module for customization purposes.
Consider using the :class:`~s3fm.api.config.Config` to customize the experience.

However, it's recommended to import the :class:`App` for type hinting purposes when
using the :class:`~s3fm.api.config.Config`.
"""
import asyncio
from typing import TYPE_CHECKING, Dict

from prompt_toolkit.application import Application
from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, VSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Frame

from s3fm.api.config import Config
from s3fm.api.history import History
from s3fm.api.kb import KB
from s3fm.exceptions import Bug
from s3fm.id import ID, Direction, LayoutMode, Pane
from s3fm.ui.commandpane import CommandPane
from s3fm.ui.filepane import FilePane
from s3fm.ui.optionpane import OptionPane

if TYPE_CHECKING:
    from prompt_toolkit.layout.containers import Container


class App:
    """Main app class to render the UI and run the application.

    It holds the top level layout of the UI and also contains several
    useful public method that user can leverage in their own customization.

    Its a bridge between all UI element and acts like a root level which
    has access to the entire application states. Similar to a app.js
    in React.js.

    Args:
        config: A :class:`~s3fm.api.config.Config` instance.
        no_history: Skip reading history.
            :class:`~s3fm.api.history.History` won't be loaded.
    """

    def __init__(self, config: Config, no_history: bool = False) -> None:
        self._style = Style.from_dict(dict(config.style))
        self._rendered = False
        self._no_history = no_history
        self._layout_mode = LayoutMode.vertical
        self._border = config.app.border
        self._current_focus = Pane.left
        self._previous_focus = None
        self._filepane_focus = Pane.left
        self._custom_effects = config.app.custom_effects
        self._history = History(
            dir_max_size=config.history.dir_max_size,
            cmd_max_size=config.history.cmd_max_size,
        )

        self._command_mode = Condition(lambda: self._current_focus == Pane.cmd)
        self._normal_mode = Condition(
            lambda: self._current_focus == Pane.left
            or self._current_focus == Pane.right
        )
        self._layout_single = Condition(lambda: self._layout_mode == LayoutMode.single)
        self._layout_vertical = Condition(
            lambda: self._layout_mode == LayoutMode.vertical
        )

        self._left_pane = FilePane(
            pane_id=Pane.left,
            spinner_config=config.spinner,
            linemode_config=config.linemode,
            app_config=config.app,
            redraw=self.redraw,
            layout_single=self._layout_single,
            layout_vertical=self._layout_vertical,
            focus=lambda: self._filepane_focus,
            history=self._history,
        )
        self._right_pane = FilePane(
            pane_id=Pane.right,
            spinner_config=config.spinner,
            linemode_config=config.linemode,
            app_config=config.app,
            redraw=self.redraw,
            layout_single=self._layout_single,
            layout_vertical=self._layout_vertical,
            focus=lambda: self._filepane_focus,
            history=self._history,
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

    def redraw(self) -> None:
        """Instruct the app to redraw itself to the terminal.

        This is useful when trying to force an UI update of the :class:`App`.
        """
        self._app.invalidate()

    async def _load_pane_data(self, pane: FilePane) -> None:
        """Load the data for the target pane and refersh the app.

        Args:
            pane: A `FilePane` instance to load data.
        """
        await pane.load_data()
        self.redraw()

    async def _render_task(self) -> None:
        """Read history and instruct left/right pane to load appropriate data.

        When `App` is created, `KB` is not activated and will only be activated
        once `History` is processed. This decision is made because `Hache` may
        cause the `App` UI to change and confuse the user.
        """
        if not self._no_history:
            await self._history.read()
        self._left_pane.mode = self._history.left_mode
        self._right_pane.mode = self._history.right_mode
        self._left_pane.selected_file_index = self._history.left_index
        self._right_pane.selected_file_index = self._history.right_index
        self._left_pane.path = self._history.left_path
        self._right_pane.path = self._history.right_path
        self.focus_pane(self._history.focus)
        self.switch_layout(self._history.layout)
        self._kb.activated = True
        await asyncio.gather(
            self._load_pane_data(pane=self._left_pane),
            self._load_pane_data(pane=self._right_pane),
        )

    def _after_render(self, _) -> None:
        """Run this function every time the `App` is re-rendered, same as `useEffect` in react.js.

        Using a class state `self._rendered` to force this function to only run once when
        the `App` is first created.

        Loading all relevant data in this method can turn the whole data loading into an
        async experience.
        """
        for use_effect in self._custom_effects:
            use_effect(self)
        if not self._rendered:
            self._rendered = True
            self._left_pane.loading = True
            self._right_pane.loading = True
            asyncio.create_task(self._render_task())

    async def run(self) -> None:
        """Start the application in async mode."""
        await self._app.run_async()

    def focus_pane(self, pane_id: ID) -> None:
        """Focus specified pane and set the focus state.

        Args:
            pane_id (ID): An :ref:`pages/configuration:ID` of the pane to focus.
                E.g. `Pane.left`.
        """
        if pane_id in self.filepanes:
            self._filepane_focus = pane_id
        self._previous_focus = self._current_focus
        self._current_focus = pane_id
        self._app.layout.focus(self.current_focus)

    def focus_other_pane(self) -> None:
        """Focus the other filepane.

        Theres only a maximum of 2 filepane in the app currently. Use
        this method to focus the other filepane.

        This method won't have any effect if the current UI only have
        one filepane.
        """
        if not self._layout_single():
            self.focus_pane(
                Pane.left if self._current_focus == Pane.right else Pane.right
            )

    def focus_cmd(self) -> None:
        """Focus the commandpane."""
        self.focus_pane(Pane.cmd)

    def exit_cmd(self) -> None:
        """Exit the commandpane and refocus the last focused filepane."""
        self.focus_pane(self._previous_focus or Pane.left)

    def exit(self) -> None:
        """Exit the application and kill all spawed processes."""
        self._history.left_mode = self._left_pane.mode
        self._history.right_mode = self._right_pane.mode
        self._history.left_index = self._left_pane.selected_file_index
        self._history.right_index = self._right_pane.selected_file_index
        self._history.left_path = self._left_pane.path
        self._history.right_path = self._right_pane.path
        self._history.focus = self._filepane_focus
        self._history.layout = self._layout_mode
        if not self._no_history:
            self._history.write()
        self._app.exit()

    def switch_layout(self, layout_id: ID) -> None:
        """Switch to a different layout.

        Args:
            layout_id (ID): An :ref:`pages/configuration:ID` of the layout.
                E.g. `LayoutMode.vertical`.
        """
        self._layout_mode = layout_id
        if layout_id != LayoutMode.single:
            self._app.layout = self.layout
            self.focus_pane(self._current_focus)

    def pane_swap(self, direction_id: ID, layout_id: ID) -> None:
        """Swap panes left/right/up/down.

        This has side effects where it may cuase layout to change.
        When current layout is `LayoutMode.vertical` and switching
        up/down, layout will be changed to `LayoutMode.horizontal`.

        This function won't have any effect when theres only one filepane.

        Args:
            direction_id (ID): An :ref:`pages/configuration:ID` of the direction.
                E.g. `Direction.left`.
            layout_id (ID): An :ref:`pages/configuration:ID` of the layout.
                E.g. `LayoutMode.vertical`.
        """
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

    async def toggle_pane_hidden_files(self, value: bool = None) -> None:
        """Toggle the current focused pane display hidden file status.

        Use this method to either instruct the current focused pane to show
        hidden files or hide hidden files.

        If current highlighted file is a hidden file and the focused pane
        is instructed to hide hidden file, highlight will shift down until
        a non hidden file.

        Args:
            value: Optional bool value to indicate show/hide.
                If not provided, it will toggle the hidden file status.
        """
        self.current_filepane.display_hidden_files = (
            value or not self.current_filepane.display_hidden_files
        )
        await self.current_filepane.filter_files()
        self.redraw()

    @property
    def command_mode(self) -> Condition:
        """:class:`prompt_toolkit.filters.Condition`: A callable if current focus is commandpane."""
        return self._command_mode

    @property
    def normal_mode(self) -> Condition:
        """:class:`prompt_toolkit.filters.Condition`: A callable if current focus is a filepane."""
        return self._normal_mode

    @property
    def current_focus(self) -> "Container":
        """:class:`prompt_toolkit.layout.Container`: Get current focused pane."""
        return {
            **self.filepanes,
            Pane.cmd: self._command_pane,
        }[self._current_focus]

    @property
    def current_filepane(self) -> FilePane:
        """:class:`~s3fm.ui.filepane.FilePane`: Get current focused filepane."""
        return self.filepanes[self._filepane_focus]

    @property
    def filepanes(self) -> Dict[ID, FilePane]:
        """Dict[ID, Container]: Get pane mappings."""
        return {
            Pane.left: self._left_pane,
            Pane.right: self._right_pane,
        }

    @property
    def layout(self) -> Layout:
        """:class:`prompt_toolkit.layout.Layout`: Get app layout dynamically.

        Raises:
            Bug: When layout mode is not recognized.
        """
        if self._layout_mode == LayoutMode.vertical:
            layout = HSplit(
                [VSplit([self._left_pane, self._right_pane]), self._command_pane]
            )

        elif (
            self._layout_mode == LayoutMode.horizontal
            or self._layout_mode == LayoutMode.single
        ):
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

    @property
    def kb(self) -> KB:
        """:class:`~s3fm.api.kb.KB`: KeyBindings."""
        return self._kb

    @property
    def rendered(self) -> bool:
        """bool: :class:`App` rendered status."""
        return self._rendered
