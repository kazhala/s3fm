from pathlib import Path

import pytest
from prompt_toolkit.layout.dimension import LayoutDimension
from pytest_mock.plugin import MockerFixture

from s3fm.api.file import File
from s3fm.app import App
from s3fm.enums import FileType, Pane, PaneMode
from s3fm.exceptions import Bug, ClientError
from s3fm.ui.filepane import FilePane, file_action, hist_dir, spin_spinner


@pytest.fixture
@pytest.mark.asyncio
async def patched_app(app: App, mocker: MockerFixture):
    mocked_height = mocker.patch.object(FilePane, "_get_height")
    mocked_height.return_value = 5
    app._left_pane._files = [
        File(name="%s" % i, type=i, info="", hidden=False, raw=Path(), index=i)
        for i in range(6)
    ]
    await app._left_pane.filter_files()
    yield app


@pytest.mark.asyncio
async def test_hist_dir_no_cd(app: App):
    @hist_dir
    async def no_cd(filepane):
        pass

    assert app._left_pane._history._directory == {}
    await no_cd(app._left_pane)
    assert app._left_pane._history._directory == {".": 0}

    app._right_pane._history._directory = {".": 12}
    await no_cd(app._right_pane)
    assert app._right_pane._history._directory == {".": 12}


@pytest.mark.asyncio
async def test_hist_dir_cd(app: App):
    @hist_dir
    async def cd(filepane: FilePane):
        filepane._fs.path = Path().absolute().root

    curr_path = app._left_pane._fs.path
    app._left_pane._mode = PaneMode.fs
    app._left_pane.selected_file_index = 1
    assert app._left_pane._history._directory == {}
    await cd(app._left_pane)
    assert app._left_pane._history._directory == {str(curr_path): 1}

    curr_path = app._right_pane._fs.path
    app._right_pane._mode = PaneMode.fs
    app._right_pane._history._directory = {".": 12}
    await cd(app._right_pane)
    assert app._left_pane._history._directory == {".": 12, str(curr_path): 0}


@pytest.mark.asyncio
async def test_spin_spinner(app: App, mocker: MockerFixture):
    @spin_spinner
    async def spin(filepane: FilePane):
        assert filepane.loading == True

    await spin(app._left_pane)
    assert app._left_pane.loading == False


@pytest.mark.asyncio
async def test_file_action(app: App, mocker: MockerFixture):
    @file_action
    async def file_operation(filepane: FilePane):
        assert True == False

    await file_operation(app._left_pane)

    mocked_selection = mocker.patch.object(FilePane, "current_selection")
    mocked_selection.return_value = None
    with pytest.raises(AssertionError):
        await file_operation(app._left_pane)


def test_get_pane_info(app: App):
    assert app._left_pane._get_pane_info() == []
    assert app._right_pane._get_pane_info() == []
    app._right_pane.mode = PaneMode.fs

    app._left_pane._loaded = True
    assert app._left_pane.mode == PaneMode.s3
    assert app._left_pane._get_pane_info() == [("class:filepane.focus_path", "s3://")]

    app._right_pane._loaded = True
    assert app._right_pane.mode == PaneMode.fs
    assert app._right_pane._get_pane_info() == [
        (
            "class:filepane.unfocus_path",
            str(app._right_pane._fs.path).replace(str(Path("~").expanduser()), "~"),
        )
    ]

    with pytest.raises(Bug):
        app._left_pane.mode = 3
        app._left_pane._get_pane_info()


class TestGetFormattedFiles:
    output1 = [
        ("[SetCursorPosition]", ""),
        ("class:filepane.current_line class:filepane.bucket", " \uf171 "),
        ("class:filepane.current_line class:filepane.bucket", "0"),
        ("class:filepane.current_line class:filepane.bucket", ""),
        ("class:filepane.current_line class:filepane.bucket", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.dir", " \uf413 "),
        ("class:filepane.other_line class:filepane.dir", "1"),
        ("class:filepane.other_line class:filepane.dir", ""),
        ("class:filepane.other_line class:filepane.dir", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.file", " \uf4a5 "),
        ("class:filepane.other_line class:filepane.file", "2"),
        ("class:filepane.other_line class:filepane.file", ""),
        ("class:filepane.other_line class:filepane.file", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.link", " \uf481 "),
        ("class:filepane.other_line class:filepane.link", "3"),
        ("class:filepane.other_line class:filepane.link", ""),
        ("class:filepane.other_line class:filepane.link", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.dir_link", " \uf482 "),
        ("class:filepane.other_line class:filepane.dir_link", "4"),
        ("class:filepane.other_line class:filepane.dir_link", ""),
        ("class:filepane.other_line class:filepane.dir_link", ""),
    ]

    output2 = [
        ("class:filepane.other_line class:filepane.dir", " \uf413 "),
        ("class:filepane.other_line class:filepane.dir", "1"),
        ("class:filepane.other_line class:filepane.dir", ""),
        ("class:filepane.other_line class:filepane.dir", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.file", " \uf4a5 "),
        ("class:filepane.other_line class:filepane.file", "2"),
        ("class:filepane.other_line class:filepane.file", ""),
        ("class:filepane.other_line class:filepane.file", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.link", " \uf481 "),
        ("class:filepane.other_line class:filepane.link", "3"),
        ("class:filepane.other_line class:filepane.link", ""),
        ("class:filepane.other_line class:filepane.link", ""),
        ("", "\n"),
        ("class:filepane.other_line class:filepane.dir_link", " \uf482 "),
        ("class:filepane.other_line class:filepane.dir_link", "4"),
        ("class:filepane.other_line class:filepane.dir_link", ""),
        ("class:filepane.other_line class:filepane.dir_link", ""),
        ("", "\n"),
        ("[SetCursorPosition]", ""),
        ("class:filepane.current_line class:filepane.exe", " \uf489 "),
        ("class:filepane.current_line class:filepane.exe", "5"),
        ("class:filepane.current_line class:filepane.exe", ""),
        ("class:filepane.current_line class:filepane.exe", ""),
    ]

    def test_no_files(self, app: App):
        assert app._left_pane.file_count == 0
        assert app._left_pane._get_formatted_files() == []

    @pytest.mark.asyncio
    async def test_index_fix(self, app: App, mocker: MockerFixture):
        mocked_height = mocker.patch.object(FilePane, "_get_height")
        mocked_height.return_value = 10

        app._left_pane._width = 10
        app._left_pane._selected_file_index = -1
        app._left_pane._files = [
            File(
                name="hello",
                type=FileType.dir,
                info="",
                hidden=False,
                raw=Path(),
                index=0,
            )
        ]
        await app._left_pane.filter_files()
        assert app._left_pane.file_count == 1
        assert app._left_pane._get_formatted_files() == [
            ("[SetCursorPosition]", ""),
            ("class:filepane.current_line class:filepane.dir", " \uf413 "),
            ("class:filepane.current_line class:filepane.dir", "hello"),
            ("class:filepane.current_line class:filepane.dir", "  "),
            ("class:filepane.current_line class:filepane.dir", ""),
        ]
        assert app._left_pane._selected_file_index == 0

        app._left_pane._selected_file_index = 2
        app._left_pane._get_formatted_files()
        assert app._left_pane._selected_file_index == 0

    def test_line_fix1(self, patched_app: App):
        patched_app._left_pane._last_line = 4
        assert patched_app._left_pane._get_formatted_files() == self.output1
        assert patched_app._left_pane._last_line == 5
        assert patched_app._left_pane._first_line == 0

    def test_line_fix2(self, patched_app: App):
        patched_app._left_pane.selected_file_index = 0
        patched_app._left_pane._first_line = 1
        patched_app._left_pane._last_line = 6
        assert patched_app._left_pane._get_formatted_files() == self.output1
        assert patched_app._left_pane._first_line == 0
        assert patched_app._left_pane._last_line == 5

    def test_line_fix3(self, patched_app: App):
        patched_app._left_pane.selected_file_index = 6
        patched_app._left_pane._first_line = 0
        patched_app._left_pane._last_line = 5
        assert patched_app._left_pane._get_formatted_files() == self.output2
        assert patched_app._left_pane._first_line == 1
        assert patched_app._left_pane._last_line == 6
        assert patched_app._left_pane.selected_file_index == 5

    def test_line_fix4(self, patched_app: App):
        patched_app._left_pane.selected_file_index = 8
        patched_app._left_pane._first_line = 2
        patched_app._left_pane._last_line = 7
        assert patched_app._left_pane._get_formatted_files() == self.output2
        assert patched_app._left_pane._first_line == 1
        assert patched_app._left_pane._last_line == 6
        assert patched_app._left_pane.selected_file_index == 5

    def test_line_fix5(self, patched_app: App):
        patched_app._left_pane._first_line = -1
        patched_app._left_pane._last_line = 1
        assert patched_app._left_pane._get_formatted_files() == self.output1
        assert patched_app._left_pane._first_line == 0
        assert patched_app._left_pane._last_line == 5


class TestGetFileInfo:
    def test_file(self, app: App):
        assert (
            app._left_pane._get_file_info(
                File(
                    name="Hello",
                    type=FileType.file,
                    info="",
                    hidden=False,
                    index=0,
                    raw=None,
                )
            )
            == ("class:filepane.file", " \uf4a5 ", "Hello", "")
        )

        assert (
            app._left_pane._get_file_info(
                File(
                    name="Hello.js",
                    type=FileType.file,
                    info="",
                    hidden=False,
                    index=0,
                    raw=None,
                )
            )
            == ("class:filepane.file", " \ue60c ", "Hello.js", "")
        )

    def test_dir(self, app: App):
        assert (
            app._left_pane._get_file_info(
                File(
                    name="Downloads",
                    type=FileType.file,
                    info="",
                    hidden=False,
                    index=0,
                    raw=None,
                )
            )
            == ("class:filepane.file", " \uf74c ", "Downloads", "")
        )

    def test_line_process_bug(self, app: App):
        @app._left_pane._linemode.register
        def _(file):
            return ("hello",)

        with pytest.raises(ClientError):
            app._left_pane._get_file_info(
                File(
                    name="Downloads",
                    type=FileType.link,
                    info="",
                    hidden=False,
                    index=0,
                    raw=None,
                )
            )

    def test_line_process(self, app: App):
        @app._left_pane._linemode.register
        def _(file):
            return None

        @app._left_pane._linemode.register
        def _(file):
            return ("class:filepane.file", "   ", file.name, file.info)

        assert (
            app._left_pane._get_file_info(
                File(
                    name="Downloads",
                    type=FileType.file,
                    info="",
                    hidden=False,
                    index=0,
                    raw=None,
                )
            )
            == ("class:filepane.file", "   ", "Downloads", "")
        )


def test_get_width_dimension(app: App, mocker: MockerFixture):
    mocked_dimension = mocker.patch("s3fm.ui.filepane.get_dimension")
    mocked_dimension.return_value = (19, 10)

    assert app._left_pane._id == Pane.left
    assert app._left_pane._padding == 1
    app._left_pane._get_width_dimension()
    assert app._left_pane._width == 9

    assert app._right_pane._id == Pane.right
    assert app._right_pane._padding == 1
    app._right_pane._get_width_dimension()
    assert app._right_pane._width == 8


def test_get_height_dimension(app: App, mocker: MockerFixture):
    mocked_dimension = mocker.patch("s3fm.ui.filepane.get_dimension")
    mocked_dimension.return_value = (19, 10)

    dimension = app._left_pane._get_height_dimension()
    assert isinstance(dimension, LayoutDimension)


def test_get_height(app: App, mocker: MockerFixture):
    mocked_dimension = mocker.patch("s3fm.ui.filepane.get_dimension")
    mocked_dimension.return_value = (19, 10)

    app._left_pane._vertical_mode = lambda: True
    assert app._left_pane._dimension_offset == 0
    assert app._left_pane._get_height() == 10

    app._left_pane._vertical_mode = lambda: False
    app._left_pane._single_mode = lambda: True
    assert app._left_pane._get_height() == 10

    app._left_pane._single_mode = lambda: False
    app._left_pane._vertical_mode = lambda: False
    app._right_pane._single_mode = lambda: False
    app._right_pane._vertical_mode = lambda: False
    assert app._right_pane._get_height() == 4
    assert app._left_pane._get_height() == 4

    mocked_dimension.return_value = (19, 11)
    assert app._left_pane._get_height() == 5
    assert app._right_pane._get_height() == 4


def test_scroll_down(patched_app: App, mocker: MockerFixture):
    assert patched_app._left_pane._selected_file_index == 0
    assert patched_app._left_pane.file_count == 6

    patched_app._left_pane.scroll_down(bottom=True)
    assert patched_app._left_pane._selected_file_index == 5

    assert patched_app._left_pane._cycle == False
    patched_app._left_pane.scroll_down()
    assert patched_app._left_pane._selected_file_index == 5

    patched_app._left_pane._cycle = True
    assert patched_app._left_pane._cycle == True
    patched_app._left_pane.scroll_down()
    assert patched_app._left_pane._selected_file_index == 0

    patched_app._left_pane.scroll_down(value=7)
    assert patched_app._left_pane._selected_file_index == 5
    patched_app._left_pane.scroll_down()
    assert patched_app._left_pane._selected_file_index == 0

    patched_app._left_pane.scroll_down(page=True)
    assert patched_app._left_pane._selected_file_index == 2


def test_scroll_up(patched_app: App, mocker: MockerFixture):
    assert patched_app._left_pane._selected_file_index == 0
    assert patched_app._left_pane.file_count == 6
    assert patched_app._left_pane._cycle == False
    patched_app._left_pane.scroll_up()
    assert patched_app._left_pane._selected_file_index == 0

    patched_app._left_pane._cycle = True
    assert patched_app._left_pane._cycle == True
    patched_app._left_pane.scroll_up()
    assert patched_app._left_pane._selected_file_index == 5

    patched_app._left_pane.scroll_up(top=True)
    assert patched_app._left_pane._selected_file_index == 0
    patched_app._left_pane.scroll_up()
    assert patched_app._left_pane._selected_file_index == 5

    patched_app._left_pane.scroll_up(page=True)
    assert patched_app._left_pane._selected_file_index == 3


def test_page_up(patched_app: App, mocker: MockerFixture):
    patched_app._left_pane._selected_file_index = 0
    patched_app._left_pane._first_line = 0
    patched_app._left_pane._last_line = 10
    patched_app._left_pane.page_up()
    assert patched_app._left_pane._selected_file_index == 0
    assert patched_app._left_pane._first_line == 0
    assert patched_app._left_pane._last_line == 10

    patched_app._left_pane._selected_file_index = 2
    patched_app._left_pane._first_line = 2
    patched_app._left_pane._last_line = 12
    patched_app._left_pane.page_up(2)
    assert patched_app._left_pane._selected_file_index == 0
    assert patched_app._left_pane._first_line == 0
    assert patched_app._left_pane._last_line == 10


def test_page_down(patched_app: App, mocker: MockerFixture):
    patched_app._left_pane._selected_file_index = 0
    patched_app._left_pane._first_line = 0
    patched_app._left_pane._last_line = 10
    patched_app._left_pane.page_down(2)
    assert patched_app._left_pane._selected_file_index == 2
    assert patched_app._left_pane._first_line == 2
    assert patched_app._left_pane._last_line == 12

    assert patched_app._left_pane.file_count == 6
    patched_app._left_pane.page_down(6)
    assert patched_app._left_pane._selected_file_index == 5
