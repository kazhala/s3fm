"""Module contains the floating loading spinner pane."""
import asyncio
from typing import Callable, List, Optional, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, Float, Window
from prompt_toolkit.layout.controls import FormattedTextControl


class Spinner(Float):
    """Display spinner in a floating window.

    Each `Spinner` is assigned to a :class:`~s3fm.api.filepane.FilePane` so that
    they can spin individually.

    Args:
        loading: :class:`prompt_toolkit.filters.Condition` to indicate if it should spin.
        redraw: A callable from :class:`~s3fm.app.App` to force UI redraw.
        pattern: A list of str to display when spinning.
        delay: Delay time between refersh.
        top: Distance from top of the container.
        bottom: Distance from bottom of the container.
        left: Distance from left of the container.
        right: Distance from right of the container.
        text: Loading text to display.
    """

    def __init__(
        self,
        loading: Condition,
        redraw: Callable[[], None],
        pattern: List[str] = None,
        delay: float = None,
        top: Optional[int] = None,
        bottom: Optional[int] = None,
        left: Optional[int] = None,
        right: Optional[int] = None,
        text: str = "",
    ) -> None:
        self._loading = loading
        self._redraw = redraw
        self._pattern = pattern or ["|", "/", "-", "\\"]
        self._char = self._pattern[0]
        self._spinning = False
        self._delay = delay or 0.1
        self._text = text

        window = Window(
            content=FormattedTextControl(text=self._get_text),
        )

        super().__init__(
            content=ConditionalContainer(
                content=window,
                filter=self._loading,
            ),
            right=right,
            top=top,
            bottom=bottom,
            left=left,
        )

    def _get_text(self) -> List[Tuple[str, str]]:
        """Get the loading char.

        Returns:
            A list of tuples which can be parsed as
            :class:`prompt_toolkit.formatted_text.FormattedText`.
        """
        return [
            ("class:spinner.pattern", self._char),
            ("class:spinner.text", self._text),
        ]

    async def start(self) -> None:
        """Run spinner."""
        if self._spinning:
            return
        self._spinning = True
        while self._loading():
            for char in self._pattern:
                await asyncio.sleep(self._delay)
                self._char = char
                self._redraw()
        self._spinning = False
