"""Module contains the pane which functions as the commandline."""
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension

from s3fm.base import BasePane


class CommandPane(BasePane):
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
