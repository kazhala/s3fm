"""Module contains the floating loading spinner pane."""
import asyncio
from itertools import zip_longest
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, Float, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets.base import Frame


class Spinner(Float):
    """Display spinner in a floating window.

    Each `Spinner` is assigned to a :class:`~s3fm.api.filepane.FilePane` so that
    they can spin individually.

    Args:
        loading: :class:`prompt_toolkit.filters.Condition` to indicate if it should spin.
        redraw: A callable from :class:`~s3fm.app.App` to force UI redraw.
        prefix_pattern: A list of str to display infront of the spinner when spinning.
        postfix_pattern: A list of pattern to display behind the spinner when spinning.
        text: The text to display when spinning.
        border: Enable border around the spinner.
    """

    def __init__(
        self,
        loading: Condition,
        redraw: Callable[[], None],
        prefix_pattern: List[str] = None,
        postfix_pattern: List[str] = None,
        text: str = " Loading ",
        border: bool = True,
    ) -> None:
        self._loading = loading
        self._redraw = redraw
        self._prefix_pattern = prefix_pattern or ["|", "/", "-", "\\"]
        self._postfix_pattern = postfix_pattern or [".   ", "..  ", "... ", "...."]
        self._text = text
        self._prefix = self._prefix_pattern[0]
        self._postfix = self._postfix_pattern[0]

        window = Window(content=FormattedTextControl(text=self._get_text))
        if border:
            window = Frame(window)

        super().__init__(
            content=ConditionalContainer(
                content=window,
                filter=self._loading,
            ),
        )

    def _get_text(self) -> List[Tuple[str, str]]:
        """Get the loading text.

        Returns:
            A list of tuples which can be parsed as
            :class:`prompt_toolkit.formatted_text.FormattedText`.
        """
        return [
            ("class:spinner.prefix", self._prefix),
            ("class:spinner.text", self._text),
            ("class:spinner.postfix", self._postfix),
        ]

    async def spin(self) -> None:
        """Run spinner."""
        while self._loading():
            for prefix, postfix in zip_longest(
                self._prefix_pattern, self._postfix_pattern, fillvalue=" "
            ):
                await asyncio.sleep(0.1)
                self._prefix = prefix
                self._postfix = postfix
                self._redraw()
