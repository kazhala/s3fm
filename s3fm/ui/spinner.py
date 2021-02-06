"""Module contains the floating loading spinner pane."""
import asyncio
from itertools import zip_longest
from typing import Callable, List

from prompt_toolkit.filters.base import FilterOrBool
from prompt_toolkit.layout.containers import ConditionalContainer, Float, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets.base import Frame

from s3fm.typings import FormattedText


class Spinner(Float):
    """Display spinner in a floating window."""

    def __init__(
        self,
        is_loading: FilterOrBool,
        prefix_pattern: List[str] = None,
        postfix_pattern: List[str] = None,
        text: str = "Loading",
        border: bool = True,
    ) -> None:
        """Initialise the UI options."""
        self._is_loading = is_loading
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
                filter=self._is_loading,
            ),
        )

    def _get_text(self) -> FormattedText:
        """Get the loading text in FormattedText.

        :return: a list of tuple as FormattedText
        :rtype: FormattedText
        """
        return [("", "%s %s %s" % (self._prefix, self._text, self._postfix))]

    async def spin(self, re_render: Callable[[], None]) -> None:
        """Run spinner.

        :param re_render: application re-render function
            used to force the application to re-render
        :type re_render: Callable[[], None]
        """
        while self._is_loading():  # type: ignore
            for prefix, postfix in zip_longest(
                self._prefix_pattern, self._postfix_pattern, fillvalue=" "
            ):
                await asyncio.sleep(0.1)
                self._prefix = prefix
                self._postfix = postfix
                re_render()
