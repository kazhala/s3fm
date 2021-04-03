import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.layout.containers import FloatContainer, VSplit
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.widgets.base import Frame
from pytest_mock.plugin import MockerFixture

from s3fm.api.config import Config
from s3fm.app import App
from s3fm.exceptions import Bug
from s3fm.id import LayoutMode


@pytest.fixture
def app():
    with create_app_session(input=create_pipe_input(), output=DummyOutput()):
        config = Config()
        app = App(config=config)
        yield app


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
