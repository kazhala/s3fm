"""Module contains the pane which functions as the commandline."""
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension


class CommandPane(Window):
    """Bottom command line pane."""

    def __init__(self) -> None:
        """Initialise the commandpane buffers."""
        super().__init__(
            BufferControl(buffer=Buffer()), height=LayoutDimension.exact(1)
        )
