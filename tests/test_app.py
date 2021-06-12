import pytest
from prompt_toolkit.application.application import Application
from prompt_toolkit.layout.containers import FloatContainer, VSplit
from prompt_toolkit.widgets.base import Frame
from pytest_mock.plugin import MockerFixture

from s3fm.api.history import History
from s3fm.api.kb import KB
from s3fm.app import App
from s3fm.enums import Direction, ErrorType, LayoutMode, Pane, PaneMode
from s3fm.exceptions import Bug, Notification
from s3fm.ui.filepane import FilePane


class TestAppLayout:
    def test_vertical_layout(self, app, mocker: MockerFixture):
        assert app._layout_mode == LayoutMode.vertical
        spy = mocker.spy(VSplit, "__init__")
        layout = app.layout
        assert isinstance(layout.container, FloatContainer) == True
        assert spy.call_count == 1
        assert len(layout.container.content.children) == 2

    def test_horizontal_layout(self, app, mocker: MockerFixture):
        app._layout_mode = LayoutMode.horizontal
        assert app._layout_mode == LayoutMode.horizontal
        spy = mocker.spy(VSplit, "__init__")
        layout = app.layout
        assert spy.call_count == 0
        assert len(layout.container.content.children) == 3

    def test_single_layout(self, app, mocker: MockerFixture):
        app._layout_mode = LayoutMode.single
        assert app._layout_mode == LayoutMode.single
        spy = mocker.spy(VSplit, "__init__")
        layout = app.layout
        assert spy.call_count == 0
        assert len(layout.container.content.children) == 3

    def test_border(self, app, mocker: MockerFixture):
        spy = mocker.spy(Frame, "__init__")
        app.layout
        spy.assert_not_called()
        app._border = True
        app.layout
        spy.assert_called_once()

    def test_exception(self, app):
        app._layout_mode = 5
        app.layout
        assert app._layout_mode == LayoutMode.vertical


def test_redraw(app, mocker: MockerFixture):
    spy = mocker.spy(Application, "invalidate")
    app.redraw()
    spy.assert_called_once()


@pytest.mark.asyncio
async def test_load_pane_date(app, mocker: MockerFixture):
    class Stub:
        async def load_data(self):
            pass

    spy = mocker.spy(App, "redraw")
    await app._load_pane_data(Stub())
    spy.assert_called_once()


@pytest.mark.asyncio
async def test_render_task(app, mocker: MockerFixture):
    assert app._kb.activated == False
    spy = mocker.spy(History, "read")
    mocker.patch.object(App, "pane_focus")
    mocker.patch.object(App, "layout_switch")
    mocker.patch.object(App, "_load_pane_data")
    app._no_history = True
    await app._render_task()
    assert app._kb.activated == True
    spy.assert_not_called()

    app._no_history = False
    await app._render_task()
    spy.assert_called_once()


@pytest.mark.asyncio
async def test_after_render(app, mocker: MockerFixture):
    stub = mocker.stub("app")
    app._custom_effects = [stub]
    task = mocker.patch.object(App, "_render_task")
    mocker.patch.object(FilePane, "loading")
    app._rendered = False
    app._after_render(None)
    task.assert_called_once()
    task.reset_mock()
    app._after_render(None)
    task.assert_not_called()
    stub.assert_called_with(app)


@pytest.mark.asyncio
async def test_run(app, mocker: MockerFixture):
    mock_run = mocker.patch.object(Application, "run_async")
    await app.run()
    mock_run.assert_called_once()


class TestFocus:
    def test_focus_left(self, app, mocker: MockerFixture):
        mocked_focus = mocker.patch("prompt_toolkit.layout.Layout.focus")
        assert app._previous_focus == None
        assert app._current_focus == Pane.left
        assert app._filepane_focus == Pane.left

        app.pane_focus(Pane.left)
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.left
        assert app._filepane_focus == Pane.left

        mocked_focus.assert_called_once_with(app.current_focus)

    def test_focus_right(self, app, mocker: MockerFixture):
        mocker.patch("prompt_toolkit.layout.Layout.focus")
        app.pane_focus(Pane.right)
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

    def test_cmd_focus(self, app, mocker: MockerFixture):
        mocker.patch("prompt_toolkit.layout.Layout.focus")
        app.pane_focus(Pane.cmd)
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.cmd
        assert app._filepane_focus == Pane.left

        app.pane_focus(Pane.right)
        assert app._previous_focus == Pane.cmd
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

        app.pane_focus(Pane.cmd)
        assert app._previous_focus == Pane.right
        assert app._current_focus == Pane.cmd
        assert app._filepane_focus == Pane.right

    def test_focus_other(self, app, mocker: MockerFixture):
        mocker.patch("prompt_toolkit.layout.Layout.focus")
        app.pane_focus_other()
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

        app._layout_mode = LayoutMode.single
        app.pane_focus_other()
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

    def test_cmd_focus_func(self, app, mocker: MockerFixture):
        mocked_focus = mocker.patch.object(App, "pane_focus")
        app.cmd_focus()
        mocked_focus.assert_called_once_with(Pane.cmd)

    def test_cmd_exit(self, app, mocker: MockerFixture):
        mocked_focus = mocker.patch.object(App, "pane_focus")
        assert app._previous_focus == None
        app.cmd_exit()
        mocked_focus.assert_called_once_with(Pane.left)

        mocked_focus.reset_mock()
        app._previous_focus = Pane.right
        app.cmd_exit()
        mocked_focus.assert_called_once_with(Pane.right)


def test_exit(app, mocker: MockerFixture):
    mocker.patch.object(Application, "exit")
    mocked_hist = mocker.patch.object(History, "write")
    app._no_history = True
    app.exit()
    mocked_hist.assert_not_called()

    app._no_history = False
    app.exit()
    mocked_hist.assert_called_once()


def test_layout_switch(app, mocker: MockerFixture):
    mocked_focus = mocker.patch.object(App, "pane_focus")
    app.layout_switch(LayoutMode.single)
    mocked_focus.assert_not_called()
    assert app._layout_mode == LayoutMode.single

    app.layout_switch(LayoutMode.vertical)
    mocked_focus.assert_called_once()
    assert app._layout_mode == LayoutMode.vertical


class TestPaneSwap:
    def test_single(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        app._layout_mode = LayoutMode.single
        app.pane_swap(Direction.left, LayoutMode.vertical)
        mocked_focus1.assert_not_called()
        mocked_focus2.assert_not_called()

    def test_no_swap_right(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        app._current_focus = Pane.right
        app._layout_mode = LayoutMode.vertical
        app.pane_swap(Direction.right, LayoutMode.vertical)
        mocked_focus1.assert_not_called()
        mocked_focus2.assert_not_called()

        app._layout_mode = LayoutMode.horizontal
        app.pane_swap(Direction.down, LayoutMode.horizontal)
        mocked_focus1.assert_not_called()
        mocked_focus2.assert_not_called()

    def test_no_swap_left(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        app._current_focus = Pane.left
        app._layout_mode = LayoutMode.vertical
        app.pane_swap(Direction.left, LayoutMode.vertical)
        mocked_focus1.assert_not_called()
        mocked_focus2.assert_not_called()

        app._layout_mode = LayoutMode.horizontal
        app.pane_swap(Direction.up, LayoutMode.horizontal)
        mocked_focus1.assert_not_called()
        mocked_focus2.assert_not_called()

    def test_swap_left_swapped(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        app._current_focus = Pane.right
        assert app._current_focus == Pane.right
        assert app._layout_mode == LayoutMode.vertical
        app.pane_swap(Direction.left, LayoutMode.vertical)
        mocked_focus2.assert_called_once()
        mocked_focus1.assert_not_called()

        mocked_focus1.reset_mock()
        mocked_focus2.reset_mock()
        app._current_focus = Pane.right
        app.pane_swap(Direction.left, LayoutMode.horizontal)
        mocked_focus2.assert_called_once()
        mocked_focus1.assert_not_called()

    def test_swap_right_swapped(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        assert app._current_focus == Pane.left
        assert app._layout_mode == LayoutMode.vertical
        app.pane_swap(Direction.right, LayoutMode.vertical)
        mocked_focus2.assert_called_once()
        mocked_focus1.assert_not_called()

        app._current_focus = Pane.left
        mocked_focus1.reset_mock()
        mocked_focus2.reset_mock()
        app.pane_swap(Direction.right, LayoutMode.horizontal)
        mocked_focus2.assert_called_once()
        mocked_focus1.assert_not_called()

    def test_swap_left_noswap(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        assert app._current_focus == Pane.left
        assert app._layout_mode == LayoutMode.vertical
        app.pane_swap(Direction.left, LayoutMode.horizontal)
        mocked_focus1.assert_called_once()
        mocked_focus2.assert_not_called()

        mocked_focus1.reset_mock()
        mocked_focus2.reset_mock()
        app._current_focus = Pane.left
        app._layout_mode = LayoutMode.horizontal
        app.pane_swap(Direction.left, LayoutMode.vertical)
        mocked_focus1.assert_called_once()
        mocked_focus2.assert_not_called()

    def test_swap_right_noswap(self, app, mocker: MockerFixture):
        mocked_focus1 = mocker.patch.object(App, "pane_focus")
        mocked_focus2 = mocker.patch.object(App, "pane_focus_other")
        app._current_focus = Pane.right
        assert app._current_focus == Pane.right
        assert app._layout_mode == LayoutMode.vertical
        app.pane_swap(Direction.right, LayoutMode.horizontal)
        mocked_focus1.assert_called_once()
        mocked_focus2.assert_not_called()

        mocked_focus1.reset_mock()
        mocked_focus2.reset_mock()
        app._current_focus = Pane.right
        app._layout_mode = LayoutMode.horizontal
        app.pane_swap(Direction.right, LayoutMode.vertical)
        mocked_focus1.assert_called_once()
        mocked_focus2.assert_not_called()


@pytest.mark.asyncio
async def test_toggle_hidden_files(app):
    assert app.current_filepane.display_hidden_files == True
    await app.pane_toggle_hidden_files(False)
    assert app.current_filepane.display_hidden_files == False


@pytest.mark.asyncio
async def test_pane_switch_mode(app: App, mocker: MockerFixture):
    mocker.patch.object(FilePane, "load_data")
    assert app.current_filepane.mode == PaneMode.s3
    await app.pane_switch_mode()
    assert app.current_filepane.mode == PaneMode.fs
    await app.pane_switch_mode()
    assert app.current_filepane.mode == PaneMode.s3

    await app.pane_switch_mode(mode=PaneMode.s3)
    assert app.current_filepane.mode == PaneMode.s3
    await app.pane_switch_mode(mode=PaneMode.fs)
    assert app.current_filepane.mode == PaneMode.fs


def test_property_pane(app):
    assert app.current_filepane == app._left_pane
    assert app.current_focus == app._left_pane
    app._current_focus = Pane.right
    app._filepane_focus = Pane.right
    assert app.current_focus == app._right_pane
    assert app.current_filepane == app._right_pane
    app._current_focus = Pane.cmd
    assert app.current_focus == app._command_pane

    assert isinstance(app.kb, KB) == True
    assert app.rendered == False


def test_set_error(app: App):
    app.set_error(Notification(message="hello", error_type=ErrorType.warning))
    assert app._error == "hello"
    assert app._error_type == ErrorType.warning

    app.set_error()
    assert app._error == ""


def test_current_focus(app: App):
    app._current_focus = Pane.right
    app.current_focus

    app._current_focus = 10
    app.current_focus
    assert app._current_focus == Pane.left
    assert app._error_type == ErrorType.warning


def test_current_filepane(app: App):
    app._filepane_focus = Pane.right
    app.current_filepane
    assert app._filepane_focus == Pane.right

    app._filepane_focus = 10
    app.current_filepane
    assert app._filepane_focus == Pane.left
    assert app._error_type == ErrorType.warning
