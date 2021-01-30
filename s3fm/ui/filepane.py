"""Module contains the main left/right pane."""
import asyncio
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import FloatContainer, Window
from prompt_toolkit.layout.controls import FormattedTextControl

from s3fm.api.config import SpinnerConfig
from s3fm.ui.spinner import Spinner


class FilePane(FloatContainer):
    """The main file pane of the app."""

    def __init__(self, pane_id: int, spinner_config: SpinnerConfig):
        """Initialise the layout of file pane."""
        self._fs_mode = False
        self._choices = ["hello", "world"]
        self._loading = True

        self._is_loading = Condition(lambda: self._loading)
        self._spinner = Spinner(
            is_loading=self._is_loading,
            prefix_pattern=spinner_config.prefix_pattern,
            postfix_pattern=spinner_config.postfix_pattern,
            text=spinner_config.text,
            border=spinner_config.border,
        )

        super().__init__(
            content=Window(
                content=FormattedTextControl(
                    self._get_formatted_choices,
                    focusable=True,
                    show_cursor=True,
                ),
            ),
            floats=[self._spinner],
        )

    def _get_formatted_choices(self) -> List[Tuple[str, str]]:
        """Get content in `formatted_text` format to display.

        :return: a list of formatted choices
        :rtype: List[Tuple[str, str]]
        """
        display_choices = []

        for index, choice in enumerate(self._choices):
            display_choices.append(("class:aaa", choice))
            display_choices.append(("", "\n"))
        if display_choices:
            display_choices.pop()
        return display_choices

    async def load_data(self, fs_mode: bool = False) -> None:
        """Load the data from either s3 or local."""
        self._fs_mode = fs_mode
        if fs_mode:
            await asyncio.sleep(1.0)
        self._choices.append("adsf")
        self._loading = False
