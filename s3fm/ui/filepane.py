"""Module contains the main left/right pane."""
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import FloatContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension

from s3fm.api.config import SpinnerConfig
from s3fm.api.fs import FS
from s3fm.api.s3 import S3
from s3fm.base import ID, BasePane, PaneMode
from s3fm.exceptions import Bug
from s3fm.ui.spinner import Spinner
from s3fm.utils import get_dimmension


class FilePane(BasePane):
    """The main file pane of the app."""

    def __init__(
        self,
        pane_id: int,
        spinner_config: SpinnerConfig,
        redraw: Callable[[], None],
        dimmension_offset: int,
        layout_single: Condition,
        layout_vertical: Condition,
        focus: Callable[[], ID],
        padding: int,
    ) -> None:
        """Initialise the layout of file pane."""
        self._s3 = S3()
        self._fs = FS()
        self._mode = PaneMode.s3
        self._choices = []
        self._loading = True
        self._dimmension_offset = dimmension_offset
        self._id = pane_id
        self._single_mode = layout_single
        self._vertical_mode = layout_vertical
        self._focus = Condition(lambda: focus() == self._id)
        self._selected_choice_index = 0
        self._width = 0
        self._padding = padding

        self._spinner = Spinner(
            loading=Condition(lambda: self._loading),
            prefix_pattern=spinner_config.prefix_pattern,
            postfix_pattern=spinner_config.postfix_pattern,
            text=spinner_config.text,
            border=spinner_config.border,
            redraw=redraw,
        )

        super().__init__(
            content=FloatContainer(
                content=VSplit(
                    [
                        Window(
                            content=FormattedTextControl(" "),
                            width=LayoutDimension.exact(self._padding),
                        ),
                        HSplit(
                            [
                                Window(
                                    content=FormattedTextControl(self._get_pane_info),
                                    height=LayoutDimension.exact(1),
                                ),
                                Window(
                                    content=FormattedTextControl(
                                        self._get_formatted_choices,
                                        focusable=True,
                                        show_cursor=False,
                                    ),
                                    width=self._get_width,
                                ),
                            ]
                        ),
                        Window(
                            content=FormattedTextControl(" "),
                            width=LayoutDimension.exact(self._padding),
                        ),
                    ]
                ),
                floats=[self._spinner],
            ),
            filter=~self._single_mode | self._focus,
        )

    def _get_pane_info(self) -> List[Tuple[str, str]]:
        """Get the top panel info of the current pane."""
        display_info = []
        color_class = (
            "class:filepane.focus_path"
            if self._focus()
            else "class:filepane.unfocus_path"
        )
        if self._mode == PaneMode.s3:
            display_info.append((color_class, self._s3.uri))
        elif self._mode == PaneMode.fs:
            display_info.append((color_class, self._fs.path))
        else:
            raise Bug("unexpected pane mode.")
        return display_info

    def _get_formatted_choices(self) -> List[Tuple[str, str]]:
        """Get content in `formatted_text` format to display.

        :return: a list of formatted choices
        :rtype: List[Tuple[str, str]]
        """
        display_choices = []

        for index, choice in enumerate(self._choices):
            if index == self._selected_choice_index and self._focus():
                display_choices.append(("[SetCursorPosition]", ""))
                display_choices.append(("class:filepane.current_line", choice["Name"]))
                display_choices.append(
                    (
                        "class:filepane.current_line",
                        " " * (self._width - 1 - len(choice["Name"])),
                    )
                )
                display_choices.append(("class:filepane.current_line", "h"))
                display_choices.append(("", "\n"))
            else:
                display_choices.append(("class:filepane.other_line", choice["Name"]))
                display_choices.append(
                    (
                        "",
                        " " * (self._width - 1 - len(choice["Name"])),
                    )
                )
                display_choices.append(("class:filepane.other_line", "h"))
                display_choices.append(("", "\n"))
        if display_choices:
            display_choices.pop()
        return display_choices

    def _get_width(self) -> LayoutDimension:
        """Retrieve the width dynamically."""
        width, _ = get_dimmension(offset=self._dimmension_offset + (self._padding * 2))
        if self._vertical_mode():
            width = round((width - (self._padding * 2)) / 2)
        self._width = width
        return LayoutDimension(preferred=width)

    def handle_down(self) -> None:
        """Move selection down."""
        self._selected_choice_index = (
            self._selected_choice_index + 1
        ) % self.choice_count

    def handle_up(self) -> None:
        """Move selection up."""
        self._selected_choice_index = (
            self._selected_choice_index - 1
        ) % self.choice_count

    async def load_data(
        self, mode_id: ID = PaneMode.s3, bucket: str = None, path: str = None
    ) -> None:
        """Load the data from either s3 or local."""
        self._mode = mode_id
        if self._mode == PaneMode.s3:
            self._choices += await self._s3.get_buckets()
        elif self._mode == PaneMode.fs:
            self._choices += await self._fs.get_paths()
        else:
            raise Bug("unexpected pane mode.")
        self._loading = False

    @property
    def choice_count(self) -> int:
        """Get total choice number."""
        return len(self._choices)

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
