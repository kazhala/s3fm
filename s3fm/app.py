"""Module contains the main App class which creates the main application.

User should not directly be using this module for customization purposes.
Consider using the :class:`~s3fm.api.config.Config` to customize the experience.

However, it's recommended to import the :class:`App` for type hinting purposes when
using the :class:`~s3fm.api.config.Config`.
"""
import asyncio
from typing import TYPE_CHECKING, Dict, Optional

from prompt_toolkit.application import Application
from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, VSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets.base import Frame

from s3fm.api.config import Config
from s3fm.api.history import History
from s3fm.api.kb import KB
from s3fm.enums import Direction, ErrorType, KBMode, LayoutMode, Pane, PaneMode
from s3fm.exceptions import Notification
from s3fm.ui.commandpane import CommandPane
from s3fm.ui.error import ErrorPane
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

    def __init__(self, config: Config = None, no_history: bool = False) -> None:
        config = config or Config()
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
        self._kb_mode = KBMode.normal

        self._error_mode = Condition(lambda: self._kb_mode == KBMode.error)
        self._command_mode = Condition(lambda: self._kb_mode == KBMode.command)
        self._normal_mode = Condition(lambda: self._kb_mode == KBMode.normal)
        self._search_mode = Condition(lambda: self._kb_mode == KBMode.search)

        self._error = ""
        self._error_type = ErrorType.error
        self._error_pane = ErrorPane(
            error=self._error_mode,
            message=lambda: self._error,
            error_type=lambda: self._error_type,
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
            set_error=self.set_error,
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
            set_error=self.set_error,
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
        self.pane_focus(self._history.focus)
        self.layout_switch(self._history.layout)
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

    def pane_focus(self, pane: Pane) -> None:
        """Focus specified pane and set the focus state.

        Args:
            pane: Target pane to focus.

        Examples:
            >>> from s3fm.app import App
            >>> from s3fm.enums import Pane
            >>> app = App() # doctest: +SKIP
            >>> app.pane_focus(Pane.left) # doctest: +SKIP
        """
        if pane in self.filepanes:
            self._kb_mode = KBMode.normal
            self._filepane_focus = pane
        else:
            self._kb_mode = KBMode.command
        self._previous_focus = self._current_focus
        self._current_focus = pane
        self._app.layout.focus(self.current_focus)

    def pane_focus_other(self) -> None:
        """Focus the other filepane.

        Theres only a maximum of 2 filepane in the app currently. Use
        this method to focus the other filepane.

        This method won't have any effect if the current UI only have
        one filepane.
        """
        if not self._layout_single():
            self.pane_focus(
                Pane.left if self._current_focus == Pane.right else Pane.right
            )

    def cmd_focus(self) -> None:
        """Focus the commandpane."""
        self.pane_focus(Pane.cmd)

    def cmd_exit(self) -> None:
        """Exit the commandpane and refocus the last focused filepane."""
        self.pane_focus(self._previous_focus or Pane.left)

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

    def layout_switch(self, layout: LayoutMode) -> None:
        """Switch to a different layout.

        Args:
            layout: Desired layout mode to switch.

        Examples:
            >>> from s3fm.app import App
            >>> from s3fm.enums import LayoutMode
            >>> app = App() # doctest: +SKIP
            >>> app.layout_switch(LayoutMode.vertical) # doctest: +SKIP
        """
        self._layout_mode = layout
        if layout != LayoutMode.single:
            self._app.layout = self.layout
            self.pane_focus(self._current_focus)

    def pane_swap(self, direction: Direction, layout: LayoutMode) -> None:
        """Swap panes left/right/up/down.

        This has side effects where it may cuase layout to change.
        When current layout is `LayoutMode.vertical` and switching
        up/down, layout will be changed to `LayoutMode.horizontal`.

        This function won't have any effect when theres only one filepane.

        Args:
            direction: Desired direction to swap.
            layout: Desired layout.

        Examples:
            >>> from s3fm.app import App
            >>> from s3fm.enums import Direction, LayoutMode
            >>> app = App() # doctest: +SKIP
            >>> app.pane_swap(Direction.left, LayoutMode.vertical) # doctest: +SKIP
        """
        if self._layout_single():
            return
        if (
            self._current_focus == Pane.right
            and (direction == Direction.right or direction == Direction.down)
            and self._layout_mode == layout
        ):
            return
        if (
            self._current_focus == Pane.left
            and (direction == Direction.left or direction == Direction.up)
            and self._layout_mode == layout
        ):
            return
        pane_swapped = False
        if not (
            self._current_focus == Pane.right
            and (direction == Direction.right or direction == Direction.down)
            and self._layout_mode != layout
        ) and not (
            self._current_focus == Pane.left
            and (direction == Direction.left or direction == Direction.up)
            and self._layout_mode != layout
        ):
            pane_swapped = True
            self._left_pane, self._right_pane = self._right_pane, self._left_pane
            self._left_pane.id, self._right_pane.id = (
                self._right_pane.id,
                self._left_pane.id,
            )
        self._layout_mode = layout
        self._app.layout = self.layout
        if pane_swapped:
            self.pane_focus_other()
        else:
            self.pane_focus(self._current_focus)

    async def pane_toggle_hidden_files(self, value: bool = None) -> None:
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

    async def pane_switch_mode(self, mode: PaneMode = None) -> None:
        """Switch the pane operation mode from one to another.

        If currently is local file system mode, then switch to s3 file system mode or vice versa.

        Args:
            mode: PaneMode for the current focus pane to switch to.
                If not provided, it will switch to the alternative mode.
        """
        if mode is not None:
            self.current_filepane.mode = mode
        else:
            self.current_filepane.mode = (
                PaneMode.s3
                if self.current_filepane.mode == PaneMode.fs
                else PaneMode.fs
            )
        await self.current_filepane.load_data()
        self.current_filepane.selected_file_index = 0

    def set_error(self, exception: Optional["Notification"] = None) -> None:
        """Configure error notification for the application.

        This should only be used to set non-application error.

        Args:
            exception: A :class:`~s3fm.exceptions.Notification` instance.
        """
        if not exception:
            self._kb_mode = KBMode.normal
            self._error = ""
        else:
            self._kb_mode = KBMode.error
            self._error = str(exception)
            self._error_type = exception.type

    @property
    def command_mode(self) -> Condition:
        """:class:`prompt_toolkit.filters.Condition`: A callable if current focus is commandpane."""
        return self._command_mode

    @property
    def normal_mode(self) -> Condition:
        """:class:`prompt_toolkit.filters.Condition`: A callable if current focus is a filepane."""
        return self._normal_mode

    @property
    def error_mode(self) -> Condition:
        """:class:`prompt_toolkit.filters.Condition`: A callable if the application has error."""
        return self._error_mode

    @property
    def current_focus(self) -> "Container":
        """:class:`prompt_toolkit.layout.Container`: Get current focused pane."""
        try:
            return {
                **self.filepanes,
                Pane.cmd: self._command_pane,
                Pane.error: self._error_pane,
            }[self._current_focus]
        except KeyError:
            self.set_error(
                Notification("Unexpected focus.", error_type=ErrorType.warning)
            )
            self.pane_focus(Pane.left)
            return self.current_focus

    @property
    def current_filepane(self) -> FilePane:
        """:class:`~s3fm.ui.filepane.FilePane`: Get current focused filepane."""
        try:
            return self.filepanes[self._filepane_focus]
        except KeyError:
            self.set_error(
                Notification("Unexpected focus.", error_type=ErrorType.warning)
            )
            self._filepane_focus = Pane.left
            return self.current_filepane

    @property
    def filepanes(self) -> Dict[Pane, FilePane]:
        """Dict[Pane, FilePane]: Get pane mappings."""
        return {
            Pane.left: self._left_pane,
            Pane.right: self._right_pane,
        }

    @property
    def layout(self) -> Layout:
        """:class:`prompt_toolkit.layout.Layout`: Get app layout dynamically."""
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
            self._layout_mode = LayoutMode.vertical
            self.set_error(
                Notification("Unexpected layout.", error_type=ErrorType.warning)
            )
            return self.layout
        if self._border:
            layout = Frame(layout)
        return Layout(
            FloatContainer(
                content=layout,
                floats=[Float(content=self._option_pane), self._error_pane],
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
