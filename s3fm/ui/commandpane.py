"""Module contains the pane which functions as the commandline."""
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension


class CommandPane(ConditionalContainer):
    """Bottom command line pane."""

    def __init__(self) -> None:
        """Initialise the commandpane buffers."""
        super().__init__(
            content=Window(
                BufferControl(buffer=Buffer()),
                height=LayoutDimension.exact(1),
            ),
            filter=True,
        )
