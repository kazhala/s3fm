"""Module contains the main App class which creates the main application."""
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.layout.containers import (
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout

from .config import Config


class App:
    """Main app class which process the config and holds the top level layout."""

    def __init__(self, config: Config) -> None:
        """Process config, options and then create the application."""
        self._border = config.border
        self._layout = Layout(
            FloatContainer(
                content=HSplit(
                    [
                        VSplit(
                            [
                                Window(
                                    FormattedTextControl(FormattedText([("", "Left")]))
                                ),
                                Window(
                                    FormattedTextControl(FormattedText([("", "Right")]))
                                ),
                            ]
                        ),
                        Window(BufferControl(buffer=Buffer())),
                    ]
                ),
                floats=[
                    Float(
                        content=Window(
                            FormattedTextControl(FormattedText([("", "Options")]))
                        )
                    )
                ],
            )
        )
        self._app = Application(layout=self._layout, full_screen=True)

    async def run(self) -> None:
        """Run the application in async mode."""
        await self._app.run_async()
