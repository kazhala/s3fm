import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.application.application import Application
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.layout.containers import FloatContainer, VSplit
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.widgets.base import Frame
from pytest_mock.plugin import MockerFixture

from s3fm.api.config import Config
from s3fm.api.history import History
from s3fm.app import App
from s3fm.exceptions import Bug
from s3fm.id import LayoutMode, Pane
from s3fm.ui.filepane import FilePane


@pytest.fixture
def app():
    pipe_input = create_pipe_input()
    try:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            config = Config()
            app = App(config=config)
            yield app
    finally:
        pipe_input.close()


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
        with pytest.raises(Bug):
            app._layout_mode = 5
            app.layout


class TestRedraw:
    class Stub:
        def __init__(self, value):
            self.value = value

        def cancelled(self):
            return self.value

    def test_redraw_cancelled(self, app, mocker):
        spy = mocker.spy(Application, "invalidate")
        stub = self.Stub(True)
        app.redraw(task=stub)
        spy.assert_not_called()

    def test_redraw(self, app, mocker):
        spy = mocker.spy(Application, "invalidate")
        stub = self.Stub(False)
        app.redraw(task=stub)
        spy.assert_called_once()

    def test_redraw_empty(self, app, mocker):
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
    mocker.patch.object(App, "focus_pane")
    mocker.patch.object(App, "switch_layout")
    mocker.patch.object(App, "_load_pane_data")
    app._no_history = True
    await app._render_task()
    assert app._kb.activated == True
    spy.assert_not_called()


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

        app.focus_pane(Pane.left)
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.left
        assert app._filepane_focus == Pane.left

        mocked_focus.assert_called_once_with(app.current_focus)

    def test_focus_right(self, app, mocker: MockerFixture):
        mocker.patch("prompt_toolkit.layout.Layout.focus")
        app.focus_pane(Pane.right)
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

    def test_focus_cmd(self, app, mocker: MockerFixture):
        mocker.patch("prompt_toolkit.layout.Layout.focus")
        app.focus_pane(Pane.cmd)
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.cmd
        assert app._filepane_focus == Pane.left

        app.focus_pane(Pane.right)
        assert app._previous_focus == Pane.cmd
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

        app.focus_pane(Pane.cmd)
        assert app._previous_focus == Pane.right
        assert app._current_focus == Pane.cmd
        assert app._filepane_focus == Pane.right

    def test_focus_other(self, app, mocker: MockerFixture):
        mocker.patch("prompt_toolkit.layout.Layout.focus")
        app.focus_other_pane()
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

        app._layout_mode = LayoutMode.single
        app.focus_other_pane()
        assert app._previous_focus == Pane.left
        assert app._current_focus == Pane.right
        assert app._filepane_focus == Pane.right

    def test_focus_cmd(self, app, mocker: MockerFixture):
        mocked_focus = mocker.patch.object(App, "focus_pane")
        app.focus_cmd()
        mocked_focus.assert_called_once_with(Pane.cmd)

    def test_exit_cmd(self, app, mocker: MockerFixture):
        mocked_focus = mocker.patch.object(App, "focus_pane")
        assert app._previous_focus == None
        app.exit_cmd()
        mocked_focus.assert_called_once_with(Pane.left)

        mocked_focus.reset_mock()
        app._previous_focus = Pane.right
        app.exit_cmd()
        mocked_focus.assert_called_once_with(Pane.right)