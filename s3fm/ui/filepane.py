"""Module contains the main filepane which is used as the left/right pane."""
import asyncio
import math
from functools import wraps
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

from prompt_toolkit.filters.base import Condition
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension

from s3fm.api.config import AppConfig, LineModeConfig, SpinnerConfig
from s3fm.api.fs import FS, S3, File
from s3fm.api.fuzzy import match_exact
from s3fm.api.history import History
from s3fm.enums import ErrorType, FileType, Pane, PaneMode
from s3fm.exceptions import ClientError, Notification
from s3fm.ui.spinner import Spinner
from s3fm.utils import get_dimension


def hist_dir(func: Callable[..., Awaitable[None]]):
    """Decorate a :class:`~s3fm.ui.filepane.FilePane` method to store the path history.

    Args:
        func: Function to be wrapped to store path infomation.

    Returns:
        Decorated function.

    Examples:
        >>> @hist_dir
        ... async def _(filepane: FilePane):
        ...     pass
    """

    @wraps(func)
    async def executable(*args, **kwargs):
        curr_path = str(
            args[0]._fs._path if args[0]._mode == PaneMode.fs else args[0]._s3._path
        )
        curr_result = args[0]._history._directory.get(curr_path, 0)
        args[0]._history._directory[curr_path] = args[0]._selected_file_index
        await func(*args, **kwargs)
        new_path = str(
            args[0]._fs._path if args[0]._mode == PaneMode.fs else args[0]._s3._path
        )
        if new_path == curr_path:
            args[0]._history._directory[curr_path] = curr_result
        else:
            args[0]._selected_file_index = args[0]._history._directory.get(new_path, 0)

    return executable


def spin_spinner(func: Callable[..., Awaitable[None]]):
    """Decorate a :class:`~s3fm.ui.filepane.FilePane` method to start and stop spinner.

    Args:
        func: Function to be wrapped to start/stop spinner.

    Returns:
        Decorated function.

    Examples:
        >>> @spin_spinner
        ... async def _(filepane: FilePane):
        ...     pass
    """

    @wraps(func)
    async def executable(*args, **kwargs):
        if not args[0].loading:
            args[0].loading = True
        try:
            await func(*args, **kwargs)
        except:
            raise
        finally:
            args[0].loading = False

    return executable


def file_action(func: Callable[..., Awaitable[None]]):
    """Decorate a method related to file action.

    On loading time, :attr:`~s3fm.ui.filepane.FilePane.current_selection`
    may not exist and raise :obj:`IndexError`. Using this decorator
    to perform additional checks.

    Args:
        func: The function to decorate.

    Returns:
        Updated function with checks.

    Examples:
        >>> @file_action
        ... async def _(filepane: FilePane):
        ...     pass
    """

    @wraps(func)
    async def executable(*args, **kwargs):
        if not args[0].current_selection:
            return
        await func(*args, **kwargs)

    return executable


class FilePane(ConditionalContainer):
    """Main file pane of the app.

    FilePane has 2 modes to operate: `PaneMode.s3` and `PaneMode.fs`. The default
    mode is the s3 mode. The mode value at the moment cannot be configured via the
    :class:`~s3fm.api.config.Config` class, this value is stored to the history via
    :class:`~s3fm.api.history.History` and is retrieved on the next time the app is opened.

    Args:
        pane_id: A :class:`~s3fm.enums.Pane` indicating whether this pane
            is the left pane or right pane. This is used to detect current app focus.
        spinner_config: :class:`~s3fm.api.config.Spinner` configuration.
        linemode_config: :class:`~s3fm.api.config.LineModeConfig` instance.
        app_config: :class:`~s3fm.api.config.AppConfig` instance.
        redraw: A callale that should be provided by :class:`~s3fm.app.App` which can force
            an UI update on the app.
        layout_single: A :class:`prompt_toolkit.filters.Condition` that can be used to check
            if the current :class:`~s3fm.app.App` is single layout.
        layout_vertical: A :class:`prompt_toolkit.filters.Condition` that can be used check
            if the current :class:`~s3fm.app.App` is vertical layout.
        focus: A function to be provided by :class:`~s3fm.app.App` to be used to get current
            app focus.
        history: :class:`~s3fm.api.hisotry.History` instnace.
        set_error: A callable to be provided by :class:`~s3fm.app.App` to set error for the application.
    """

    def __init__(
        self,
        pane_id: Pane,
        spinner_config: SpinnerConfig,
        linemode_config: LineModeConfig,
        app_config: AppConfig,
        redraw: Callable[[], None],
        layout_single: Condition,
        layout_vertical: Condition,
        focus: Callable[[], Pane],
        history: History,
        set_error: Callable[[Optional[Notification]], None],
    ) -> None:
        self._s3 = S3()
        self._fs = FS()
        self._mode = PaneMode.s3
        self._loaded = False
        self._files: List[File] = []
        self._filtered_files: List[File] = []
        self._searched_indices: Optional[Dict[int, List[int]]] = None
        self._loading = True
        self._dimension_offset = 0 if not app_config.border else 2
        self._padding = app_config.padding
        self._cycle = app_config.cycle
        self._id: Pane = pane_id
        self._single_mode = layout_single
        self._vertical_mode = layout_vertical
        self._focus = Condition(lambda: focus() == self._id)
        self._selected_file_index = 0
        self._width = 0
        self._linemode = linemode_config
        self._display_hidden = True
        self._first_line = 0
        self._last_line = self._get_height() - self._first_line
        self._history = history
        self._set_error = set_error

        self._spinner = Spinner(
            loading=Condition(lambda: self._loading),
            pattern=spinner_config.pattern,
            redraw=redraw,
            delay=spinner_config.delay,
            top=spinner_config.top,
            bottom=spinner_config.bottom,
            left=spinner_config.left,
            right=spinner_config.right,
            text=spinner_config.text,
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
            Notification: When pane mode is not recognized.
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
                    str(self._fs.path).replace(str(Path("~").expanduser()), "~"),
                )
            )
        else:
            self._mode = PaneMode.fs
            self.set_error(
                Notification("Unexpected pane mode.", error_type=ErrorType.warning)
            )
            return self._get_pane_info()
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

            if self._searched_indices is not None and index in self._searched_indices:
                for j in range(len(name)):
                    if j in self._searched_indices[index]:
                        display_files.append(("class:filepane.searched", name[j]))
                    else:
                        display_files.append((style_class, name[j]))
            else:
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
            file: A :class:`~s3fm.id.File` instance.

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

    def scroll_down(
        self, value: int = 1, page: bool = False, bottom: bool = False
    ) -> None:
        """Move current selection down.

        Args:
            value: Number of lines to scroll down.
            page: Scroll half a page down.
            bottom: Scroll to bottom.
        """
        if bottom:
            self._selected_file_index = self.file_count - 1
            return
        if page:
            value = self._get_height() // 2
        if self._cycle and value == 1:
            self._selected_file_index = (
                self._selected_file_index + 1
            ) % self.file_count
        else:
            self._selected_file_index += value
            if self._selected_file_index >= self.file_count:
                self._selected_file_index = self.file_count - 1

    def scroll_up(self, value: int = 1, page: bool = False, top: bool = False) -> None:
        """Move current selection up.

        Args:
            value: Number of lines to scroll down.
            page: Scroll half a page down.
            top: Scroll to top.
        """
        if top:
            self._selected_file_index = 0
            return
        if page:
            value = self._get_height() // 2
        if self._cycle and value == 1:
            self._selected_file_index = (
                self._selected_file_index - 1
            ) % self.file_count
        else:
            self._selected_file_index -= value
            if self._selected_file_index < 0:
                self._selected_file_index = 0

    def page_up(self, value: int = 1) -> None:
        """Scroll page up.

        Slightly different scroll behavior than :meth:`FilePane.scroll_up`, similar
        to vim "c-y".

        Args:
            value: Number of lines to scroll.
        """
        if self._selected_file_index - value < 0:
            self._selected_file_index = 0
            return
        self._first_line -= value
        self._last_line -= value
        self._selected_file_index -= value

    def page_down(self, value: int = 1) -> None:
        """Scroll page down.

        Slightly different scroll behavior than :meth:`FilePane.scroll_down`, similar
        to vim "c-e".

        Args:
            value: Number of lines to scroll.
        """
        if self._selected_file_index + value >= self.file_count:
            self._selected_file_index = self.file_count - 1
            return
        self._first_line += value
        self._last_line += value
        self._selected_file_index += value

    @hist_dir
    @spin_spinner
    @file_action
    async def forward(self) -> None:
        """Handle the forward action on the current file based on filetype."""
        current_path = self.path
        if self._mode == PaneMode.fs:
            if self.current_selection.type == FileType.dir:
                try:
                    self._files = await self._fs.cd(Path(self.current_selection.name))
                except Exception as e:
                    self.set_error(Notification(str(e)))
                    self._files = await self._fs.cd(Path(current_path))
        elif self._mode == PaneMode.s3:
            if (
                self.current_selection.type == FileType.dir
                or self.current_selection.type == FileType.bucket
            ):
                try:
                    self._files = await self._s3.cd(self.current_selection.name)
                except Exception as e:
                    self.set_error(Notification(str(e)))
                    self._files = await self._fs.cd(Path(current_path))
        else:
            self._mode = PaneMode.fs
            self.set_error(
                Notification("Unexpected pane mode.", error_type=ErrorType.warning)
            )
            return await self.forward()
        await self.filter_files()

    @hist_dir
    @spin_spinner
    async def backword(self) -> None:
        """Handle the backword action.

        Raises:
            Notification: Unexpected pane mode.
        """
        if self._mode == PaneMode.fs:
            self._files = await self._fs.cd()
        elif self._mode == PaneMode.s3:
            self._files = await self._s3.cd()
        else:
            self._mode = PaneMode.fs
            self.set_error(
                Notification("Unexpected pane mode.", error_type=ErrorType.warning)
            )
            return await self.filter_files()
        await self.filter_files()

    @spin_spinner
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

    @spin_spinner
    async def load_data(self) -> None:
        """Load the data into filepane.

        Raises:
            Notification: Current pane mode is not recognized.
        """
        self._files = []
        if self._mode == PaneMode.s3:
            try:
                self._files += await self._s3.get_paths()
            except:
                self.set_error(
                    Notification(
                        message="Target S3 path %s is not valid or you do not have sufficent permissions."
                        % self._s3.path
                    )
                )
                self._s3.path = Path("")
                self._files += await self._s3.get_paths()
        elif self._mode == PaneMode.fs:
            try:
                self._files += await self._fs.get_paths()
            except:
                self.set_error(
                    Notification(
                        message="Target path %s is not a valid directory."
                        % self._fs.path
                    )
                )
                self._fs.path = Path("").resolve()
                self._files += await self._fs.get_paths()
        else:
            self._mode = PaneMode.fs
            self.set_error(
                Notification("Unexpected pane mode.", error_type=ErrorType.warning)
            )
            return await self.load_data()
        await self.filter_files()
        self._loaded = True

    def set_error(self, notification: Notification = None) -> None:
        """Set error notification for the application.

        This should only be used to set non-application error.

        Args:
            notification: A :class:`~s3fm.exceptions.Notification` instance.
        """
        self._set_error(notification)

    async def pane_toggle_hidden_files(self, value: bool = None) -> None:
        """Toggle the current focused pane display hidden file status.

        Use this method to either instruct the current focused pane to show
        hidden files or hide hidden files.

        If current highlighted file is a hidden file and the focused pane
        is instructed to hide hidden file, highlight will shift down until
        a non hidden file.

        Args:
            value: Optional bool value to indicate show/hide.
                If not provided, it will toggle the hidden file status.
        """
        self.display_hidden_files = value or not self.display_hidden_files
        await self.filter_files()

    async def pane_switch_mode(self, mode: PaneMode = None) -> None:
        """Switch the pane operation mode from one to another.

        If currently is local file system mode, then switch to s3 file system mode or vice versa.

        Args:
            mode: PaneMode for the current focus pane to switch to.
                If not provided, it will switch to the alternative mode.
        """
        if mode is not None:
            self.mode = mode
        else:
            self.mode = PaneMode.s3 if self.mode == PaneMode.fs else PaneMode.fs
        await self.load_data()
        self.selected_file_index = 0

    async def search_text(self, text: str) -> None:
        """Search text in all visible files.

        Args:
            text: Text to search.
        """
        if not text:
            self._searched_indices = None
        else:
            await asyncio.sleep(self._calculate_wait_time())
            self._searched_indices = await match_exact(self.files, text)

    def _calculate_wait_time(self) -> float:
        """Calculate wait time to smoother the application on big data set.

        Using digit of the choices lengeth to get wait time.
        For digit greater than 6, using formula 2^(digit - 5) * 0.3 to increase the wait_time.

        Still experimenting, require improvements.
        """
        wait_table = {
            2: 0.05,
            3: 0.1,
            4: 0.2,
            5: 0.3,
        }
        digit = 1
        if self.file_count > 0:
            digit = int(math.log10(self.file_count)) + 1

        if digit < 2:
            return 0.0
        if digit in wait_table:
            return wait_table[digit]
        return wait_table[5] * (2 ** (digit - 5))

    @property
    def file_count(self) -> int:
        """int: Total file count."""
        return len(self._filtered_files)

    @property
    def spinner(self) -> Spinner:
        """:class:`~s3fm.ui.spinner.Spinner`: :class:`FilePane` spinner instance."""
        return self._spinner

    @property
    def id(self) -> Pane:
        """Pane: Get the id indicating purpose of the filepane."""
        return self._id

    @id.setter
    def id(self, value: Pane) -> None:
        self._id = value

    @property
    def files(self) -> List[File]:
        """Iterable[File]: All available files to display."""
        return self._filtered_files

    @property
    def current_selection(self) -> Optional[File]:
        """File: Get current file selection.

        On filepane initialisation, if `current_selection` is requested,
        return `None`.
        """
        try:
            return self._files[self._filtered_files[self._selected_file_index].index]
        except IndexError:
            return None

    @property
    def display_hidden_files(self) -> bool:
        """bool: Hidden file display status."""
        return self._display_hidden

    @display_hidden_files.setter
    def display_hidden_files(self, value: bool) -> None:
        self._display_hidden = value

    @property
    def loading(self) -> bool:
        """bool: Loading status of the pane."""
        return self._loading

    @loading.setter
    def loading(self, value: bool) -> None:
        self._loading = value
        if value:
            asyncio.create_task(self.spinner.start())

    @property
    def mode(self) -> PaneMode:
        """PaneMode: Current pane mode."""
        return self._mode

    @mode.setter
    def mode(self, value: PaneMode) -> None:
        self._mode = value

    @property
    def selected_file_index(self) -> int:
        """int: Current selection index."""
        return self._selected_file_index

    @selected_file_index.setter
    def selected_file_index(self, value: int) -> None:
        """int: Current selection index."""
        self._selected_file_index = value

    @property
    def path(self) -> str:
        """str: Current filepath."""
        if self.mode == PaneMode.s3:
            return str(self._s3.path)
        elif self.mode == PaneMode.fs:
            return str(self._fs.path)
        else:
            self._mode = PaneMode.fs
            self.set_error(
                Notification("Unexpected pane mode.", error_type=ErrorType.warning)
            )
            return self.path

    @path.setter
    def path(self, value) -> None:
        if self.mode == PaneMode.s3:
            self._s3.path = Path(value)
        elif self.mode == PaneMode.fs:
            self._fs.path = Path(value)
        else:
            self._mode = PaneMode.fs
            self.set_error(
                Notification("Unexpected pane mode.", error_type=ErrorType.warning)
            )
            self._fs.path = Path(value)

    @property
    def searched_indices(self) -> Optional[Dict[int, List[int]]]:
        """Optional[Dict[int, List[int]]]: Dictionary of current seach result index and matching indices."""
        return self._searched_indices

    @searched_indices.setter
    def searched_indices(self, value) -> None:
        self._searched_indices = value
