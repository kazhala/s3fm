"""Module contains the main filepane which is used as the left/right pane."""
import math
from pathlib import Path
from typing import Callable, List, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import FloatContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension

from s3fm.api.config import LineModeConfig, SpinnerConfig
from s3fm.api.fs import FS
from s3fm.api.s3 import S3
from s3fm.base import ID, BasePane, File, Pane, PaneMode
from s3fm.exceptions import Bug, ClientError
from s3fm.ui.spinner import Spinner
from s3fm.utils import get_dimension


class FilePane(BasePane):
    """Main file pane of the app.

    FilePane has 2 modes to operate: `PaneMode.s3` and `PaneMode.fs`. The default
    mode is the s3 mode. The mode value at the moment cannot be configured via the
    :class:`~s3fm.api.config.Config` class, this value is stored to the cache via
    :class:`~s3fm.api.cache.Cache` and is retrieved on the next time the app is opened.

    Args:
        pane_id (ID): An :ref:`pages/configuration:ID` indicating whether this pane
            is the left pane or right pane. This is used to detect current app focus.
        spinner_config: :class:`~s3fm.api.config.Spinner` configuration.
        redraw: A callale that should be provided by :class:`~s3fm.app.App` which can force
            an UI update on the app.
        dimension_offset: Offset that should be applied to height or width.
        layout_single: A :class:`prompt_toolkit.filters.Condition` that can be used to check
            if the current :class:`~s3fm.app.App` is single layout.
        layout_vertical: A :class:`prompt_toolkit.filters.Condition` that can be used check
            if the current :class:`~s3fm.app.App` is vertical layout.
        focus: A function to be provided by :class:`~s3fm.app.App` to be used to get current
            app focus.
        padding: Padding to be applied around the file pane. This can be configured under
            :class:`~s3fm.api.config.AppConfig`.
        linemode: :class:`~s3fm.api.config.LineModeConfig` instance.
    """

    def __init__(
        self,
        pane_id: ID,
        spinner_config: SpinnerConfig,
        redraw: Callable[[], None],
        dimension_offset: int,
        layout_single: Condition,
        layout_vertical: Condition,
        focus: Callable[[], ID],
        padding: int,
        linemode: LineModeConfig,
    ) -> None:
        self._s3 = S3()
        self._fs = FS()
        self._mode = PaneMode.s3
        self._loaded = False
        self._files: List[File] = []
        self._filtered_files: List[File] = []
        self._loading = True
        self._dimension_offset = dimension_offset
        self._id = pane_id
        self._single_mode = layout_single
        self._vertical_mode = layout_vertical
        self._focus = Condition(lambda: focus() == self._id)
        self._selected_file_index = 0
        self._width = 0
        self._padding = padding
        self._linemode = linemode
        self._display_hidden = True
        self._first_line = 0
        self._last_line = self._get_height() - self._first_line

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
                                    width=self._get_width_dimension,
                                ),
                            ]
                        ),
                        Window(
                            content=FormattedTextControl(" "),
                            width=LayoutDimension.exact(self._padding),
                        ),
                    ],
                    height=self._get_height_dimension,
                ),
                floats=[self._spinner],
            ),
            filter=~self._single_mode | self._focus,
        )

    def _get_pane_info(self) -> List[Tuple[str, str]]:
        """Get the top panel info of the current pane.

        This will be used to display some information at the top of
        the filepane.

        Returns:
            A list of tuples which can be parsed as
            :class:`prompt_toolkit.formatted_text.FormattedText`.

        Raises:
            Bug: When pane mode is not recognized.
        """
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
            display_info.append(
                (
                    color_class,
                    str(self._fs.path.resolve()).replace(
                        str(Path("~").expanduser()), "~"
                    ),
                )
            )
        else:
            raise Bug("unexpected pane mode.")
        return display_info

    def _get_formatted_files(self) -> List[Tuple[str, str]]:
        """Get content in `formatted_text` format to display.

        This function will only try to return the necessary files to display
        to optimise performance.

        The files/height will be calculated dynamically based on certain conditions.

        Returns:
            A list of tuples which can be parsed as
            :class:`prompt_toolkit.formatted_text.FormattedText`.
        """
        display_files = []
        if self.file_count == 0:
            return display_files
        height = self._get_height()

        if self._selected_file_index < 0:
            self._selected_file_index = 0
        elif self._selected_file_index >= self.file_count:
            self._selected_file_index = self.file_count - 1

        if (self._last_line - self._first_line) < min(self.file_count, height):
            self._last_line = min(self.file_count, height)
            self._first_line = self._last_line - min(self.file_count, height)

        if self._selected_file_index <= self._first_line:
            self._first_line = self._selected_file_index
            self._last_line = self._first_line + min(height, self.file_count)
        elif self._selected_file_index >= self._last_line:
            self._last_line = self._selected_file_index + 1
            self._first_line = self._last_line - min(height, self.file_count)

        if self._last_line > self.file_count:
            self._last_line = self.file_count
            self._first_line = self._last_line - min(height, self.file_count)
        if self._first_line < 0:
            self._first_line = 0
            self._last_line = self._first_line + min(height, self.file_count)

        for index in range(self._first_line, self._last_line):
            file = self.files[index]
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
        """Get the file info to display.

        This is used internally by :meth:`FilePane._get_formatted_files`.

        Args:
            file: A :class:`~s3fm.base.File` instance.

        Returns:
            A tuple representing the style, icon, file_name and file_info.

        Raises:
            ClientError: When custom linemode does not return 4 values which caused
                the unpack function to raise error.
        """
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

    def _get_width_dimension(self) -> LayoutDimension:
        """Retrieve the width dimension dynamically.

        Returns:
            :class:`prompt_toolkit.layout.Dimension` instance.
        """
        width, _ = get_dimension(offset=self._dimension_offset + (self._padding * 2))
        if self._vertical_mode():
            if self._id == Pane.left:
                width = math.ceil((width - (self._padding * 2)) / 2)
            elif self._id == Pane.right:
                width = math.floor((width - (self._padding * 2)) / 2)
        self._width = width
        return LayoutDimension(preferred=width)

    def _get_height_dimension(self) -> LayoutDimension:
        """Retrieve the height dimension dynamically.

        Returns:
            :class:`prompt_toolkit.layout.Dimension` instance.
        """
        return LayoutDimension(preferred=self._get_height() + 1)

    def _get_height(self) -> int:
        """Obtain the total available height for file display.

        Returns:
            The available height to display files.
        """
        if self._vertical_mode() or self._single_mode():
            _, height = get_dimension(offset=self._dimension_offset + 2)
        else:
            _, height = get_dimension(offset=self._dimension_offset + 1)
            if self._id == Pane.left:
                height = math.ceil(height / 2) - 1
            elif self._id == Pane.right:
                height = math.floor(height / 2) - 1
        return height

    def handle_down(self) -> None:
        """Move current selection down."""
        self._selected_file_index = (self._selected_file_index + 1) % self.file_count

    def handle_up(self) -> None:
        """Move current selection up."""
        self._selected_file_index = (self._selected_file_index - 1) % self.file_count

    async def filter_files(self) -> None:
        """Shift up/down taking consideration of hidden status.

        When the filepane change its hidden display status, if the current
        highlight is a hidden file, the app will lost its highlighted line.
        Use this method to shift down until it found a file thats not hidden.
        """
        if self._display_hidden:
            self._filtered_files = self._files
        else:
            self._filtered_files = list(
                filter(lambda file: not file.hidden, self._files)
            )

    async def load_data(
        self, mode_id: ID = PaneMode.s3, bucket: str = None, path: str = None
    ) -> None:
        """Load the data into filepane.

        Provide a `mode_id` to instruct which file to load. `PaneMode.s3` will
        instruct to load the s3 data. `PaneMode.fs` will load the local file system
        data.

        Args:
            mode_id (ID): An :ref:`pages/configuration:ID` indicating which mode.
            bucket: Bucket to load the s3 data.
            path: Path to load the s3 or fs data.

        Raises:
            Bug: Current pane mode is not recognized.
        """
        self._mode = mode_id
        if self._mode == PaneMode.s3:
            self._files += await self._s3.get_buckets()
        elif self._mode == PaneMode.fs:
            self._files += await self._fs.get_paths()
        else:
            raise Bug("unexpected pane mode.")
        await self.filter_files()
        self._loading = False
        self._loaded = True

    @property
    def file_count(self) -> int:
        """int: Total file count."""
        return len(self._filtered_files)

    @property
    def spinner(self) -> Spinner:
        """:class:`~s3fm.ui.spinner.Spinner`: :class:`FilePane` spinner instance."""
        return self._spinner

    @property
    def id(self) -> ID:
        """:ref:`pages/configuration:ID`: :class:`FilePane` ID in the :class:`~s3fm.app.App`."""
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        self._id = value

    @property
    def files(self) -> List[File]:
        """Iterable[File]: All available files to display."""
        return self._filtered_files

    @property
    def current_selection(self) -> File:
        """File: Get current file selection."""
        return self._files[self._filtered_files[self._selected_file_index].index]

    @property
    def display_hidden_files(self) -> bool:
        """bool: Hidden file display status."""
        return self._display_hidden

    @display_hidden_files.setter
    def display_hidden_files(self, value: bool) -> None:
        self._display_hidden = value
