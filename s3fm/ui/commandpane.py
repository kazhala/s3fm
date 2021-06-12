"""Module contains the pane which functions as the commandline."""
from typing import List, Tuple

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.processors import BeforeInput

from s3fm.enums import CommandMode


class CommandPane(ConditionalContainer):
    """Bottom command line pane."""

    def __init__(self) -> None:
        """Initialise the commandpane buffers."""
        self._mode = CommandMode.clear
        self._buffer = Buffer()

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
