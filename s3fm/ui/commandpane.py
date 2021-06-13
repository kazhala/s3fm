"""Module contains the pane which functions as the commandline."""
import asyncio
from typing import TYPE_CHECKING, List, Tuple

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.processors import BeforeInput

from s3fm.enums import CommandMode

if TYPE_CHECKING:
    from s3fm.app import App


class CommandPane(ConditionalContainer):
    """Bottom command line pane."""

    def __init__(self, app: "App") -> None:
        """Initialise the commandpane buffers."""
        self._app = app
        self._mode = CommandMode.clear
        self._task = None
        self._buffer = Buffer(on_text_changed=self._on_text_changed)

        super().__init__(
            content=Window(
                BufferControl(
                    buffer=self._buffer,
                    input_processors=[BeforeInput(self._get_before_input)],
                ),
                height=LayoutDimension.exact(1),
            ),
            filter=True,
        )

    def _task_callback(self, task) -> None:
        if task.cancelled():
            return
        self._app.redraw()

    def _on_text_changed(self, _) -> None:
        if self._mode == CommandMode.command:
            return
        if self._task and not self._task.done():
            self._task.cancel()
        if self._mode == CommandMode.search:
            self._task = asyncio.create_task(
                self._app.current_filepane.search_text(text=self.text)
            )
            self._task.add_done_callback(self._task_callback)

    def _get_before_input(self) -> List[Tuple[str, str]]:
        if self._mode == CommandMode.search:
            return [("class:command.prefix", "/")]
        elif self._mode == CommandMode.reverse_search:
            return [("class:command.prefix", "?")]
        elif self._mode == CommandMode.command:
            return [("class:command.prefix", ":")]
        else:
            return [("", " ")]

    @property
    def buffer(self) -> Buffer:
        """Buffer: Command buffer."""
        return self._buffer

    @property
    def mode(self) -> CommandMode:
        """CommandMode: Command pane mode."""
        return self._mode

    @mode.setter
    def mode(self, value) -> None:
        self._mode = value

    @property
    def text(self) -> str:
        """str: Current cmd text."""
        return self._buffer.text
