"""Module contains the main left/right pane."""
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import FloatContainer, Window
from prompt_toolkit.layout.controls import FormattedTextControl

from s3fm.api.config import SpinnerConfig
from s3fm.api.fs import FS
from s3fm.api.s3 import S3
from s3fm.base import MODE, PaneMode
from s3fm.exceptions import Bug
from s3fm.ui.spinner import Spinner

S3_MODE = PaneMode.s3
FS_MODE = PaneMode.fs


class FilePane(FloatContainer):
    """The main file pane of the app."""

    def __init__(
        self, pane_id: int, spinner_config: SpinnerConfig, redraw: Callable[[], None]
    ) -> None:
        """Initialise the layout of file pane."""
        self._s3 = S3()
        self._fs = FS()
        self._mode = S3_MODE
        self._choices = []
        self._loading = True

        self._is_loading = Condition(lambda: self._loading)
        self._spinner = Spinner(
            is_loading=self._is_loading,
            prefix_pattern=spinner_config.prefix_pattern,
            postfix_pattern=spinner_config.postfix_pattern,
            text=spinner_config.text,
            border=spinner_config.border,
            redraw=redraw,
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

        for _, choice in enumerate(self._choices):
            display_choices.append(("class:aaa", choice))
            display_choices.append(("", "\n"))
        if display_choices:
            display_choices.pop()
        return display_choices

    async def load_data(
        self, mode: MODE = S3_MODE, bucket: str = None, path: str = None
    ) -> None:
        """Load the data from either s3 or local."""
        self._mode = mode
        if self._mode == S3_MODE:
            self._choices += await self._s3.get_buckets()
        elif self._mode == FS_MODE:
            self._choices += await self._fs.get_paths()
        else:
            raise Bug("unexpected pane mode.")
        self._loading = False

    @property
    def spinner(self) -> Spinner:
        """Get spinner."""
        return self._spinner
