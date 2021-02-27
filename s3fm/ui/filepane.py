"""Module contains the main left/right pane."""
from pathlib import Path
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import FloatContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension

from s3fm.api.config import LineModeConfig, SpinnerConfig
from s3fm.api.fs import FS
from s3fm.api.s3 import S3
from s3fm.base import ID, BasePane, File, PaneMode
from s3fm.exceptions import Bug, ClientError
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
        linemode: LineModeConfig,
    ) -> None:
        """Initialise the layout of file pane."""
        self._s3 = S3()
        self._fs = FS()
        self._mode = PaneMode.s3
        self._loaded = False
        self._files: List[File] = []
        self._loading = True
        self._dimmension_offset = dimmension_offset
        self._id = pane_id
        self._single_mode = layout_single
        self._vertical_mode = layout_vertical
        self._focus = Condition(lambda: focus() == self._id)
        self._selected_file_index = 0
        self._width = 0
        self._padding = padding
        self._linemode = linemode

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
                                        self._get_formatted_files,
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
        if not self._loaded:
            return []
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

    def _get_formatted_files(self) -> List[Tuple[str, str]]:
        """Get content in `formatted_text` format to display.

        :return: a list of formatted files ready to display
        :rtype: List[Tuple[str, str]]
        """
        display_files = []

        for index, file in enumerate(self._files):
            file_style, icon, name, info = self._get_file_info(file)
            style_class = "class:filepane.other_line"
            if index == self._selected_file_index and self._focus():
                style_class = "class:filepane.current_line"
                display_files.append(("[SetCursorPosition]", ""))
            style_class += " %s" % file_style

            display_files.append((style_class, icon))
            display_files.append((style_class, name))
            display_files.append(
                (
                    style_class,
                    " " * (self._width - len(icon) - len(name) - len(info)),
                )
            )
            display_files.append((style_class, info))
            display_files.append(("", "\n"))
        if display_files:
            display_files.pop()
        return display_files

    def _get_file_info(self, file: File) -> Tuple[str, str, str, str]:
        style_class = ""
        icon = ""
        file_name = file.name
        file_info = file.info

        for func in self._linemode.process:
            result = func(file)
            if isinstance(result, Tuple):
                try:
                    style_class, icon, file_name, file_info = result
                    return style_class, icon, file_name, file_info
                except ValueError:
                    raise ClientError(
                        "linemode process function should return a tuple of total 4 values (style_class, icon, file_name, file_info)."
                    )

        if file.type in self._linemode.filetype_maps:
            icon = self._linemode.filetype_maps[file.type]
        if file.name in self._linemode.exact_maps:
            icon = self._linemode.exact_maps[file.name]
        ext = Path(file.name).suffix
        if ext in self._linemode.extension_maps:
            icon = self._linemode.extension_maps[ext]
        style_class = self._linemode.style_maps[file.type]

        return style_class, icon, file_name, file_info

    def _get_width(self) -> LayoutDimension:
        """Retrieve the width dynamically."""
        width, _ = get_dimmension(offset=self._dimmension_offset + (self._padding * 2))
        if self._vertical_mode():
            width = round((width - (self._padding * 2)) / 2)
        self._width = width
        return LayoutDimension(preferred=width)

    def handle_down(self) -> None:
        """Move selection down."""
        self._selected_file_index = (self._selected_file_index + 1) % self.file_count

    def handle_up(self) -> None:
        """Move selection up."""
        self._selected_file_index = (self._selected_file_index - 1) % self.file_count

    async def load_data(
        self, mode_id: ID = PaneMode.s3, bucket: str = None, path: str = None
    ) -> None:
        """Load the data from either s3 or local."""
        self._mode = mode_id
        if self._mode == PaneMode.s3:
            self._files += await self._s3.get_buckets()
        elif self._mode == PaneMode.fs:
            self._files += await self._fs.get_paths()
        else:
            raise Bug("unexpected pane mode.")
        self._loading = False
        self._loaded = True

    @property
    def file_count(self) -> int:
        """Get total file count."""
        return len(self._files)

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
