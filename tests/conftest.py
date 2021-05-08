import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from s3fm.api.config import Config
from s3fm.app import App


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
