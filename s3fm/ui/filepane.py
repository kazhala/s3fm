"""Module contains the main left/right pane."""
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    FloatContainer,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension

from s3fm.api.config import SpinnerConfig
from s3fm.api.fs import FS
from s3fm.api.s3 import S3
from s3fm.base import MODE, PaneMode
from s3fm.exceptions import Bug
from s3fm.ui.spinner import Spinner
from s3fm.utils import get_dimmension

S3_MODE = PaneMode.s3
FS_MODE = PaneMode.fs


class FilePane(FloatContainer):
    """The main file pane of the app."""

    def __init__(
        self,
        pane_id: int,
        spinner_config: SpinnerConfig,
        redraw: Callable[[], None],
        dimmension_offset: int,
        layout_single: Condition,
        focus: Condition,
    ) -> None:
        """Initialise the layout of file pane."""
        self._s3 = S3()
        self._fs = FS()
        self._mode = S3_MODE
        self._choices = []
        self._loading = True
        self._dimmension_offset = dimmension_offset
        self._id = pane_id
        self._single_mode = layout_single
        self._focus = focus

        self._spinner = Spinner(
            loading=Condition(lambda: self._loading),
            prefix_pattern=spinner_config.prefix_pattern,
            postfix_pattern=spinner_config.postfix_pattern,
            text=spinner_config.text,
            border=spinner_config.border,
            redraw=redraw,
        )

        super().__init__(
            content=ConditionalContainer(
                Window(
                    content=FormattedTextControl(
                        self._get_formatted_choices,
                        focusable=True,
                        show_cursor=True,
                    ),
                    width=self._get_width,
                ),
                filter=~self._single_mode | self._focus,
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

    def _get_width(self) -> LayoutDimension:
        """Retrieve the width dynamically."""
        width, _ = get_dimmension(offset=self._dimmension_offset)
        return LayoutDimension(preferred=round(width / 2))

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

    @property
    def id(self) -> int:
        """Get pane id."""
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        """Set pane id."""
        self._id = value
