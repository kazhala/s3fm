from unittest.mock import ANY

import pytest
from prompt_toolkit.keys import Keys
from pytest_mock.plugin import MockerFixture

from s3fm.api.config import (
    AppConfig,
    BaseStyleConfig,
    KBConfig,
    LineModeConfig,
    StyleConfig,
)
from s3fm.enums import KBMode
from s3fm.exceptions import ClientError


def test_app_config():
    config = AppConfig()
    assert config.custom_effects == []

    @config.use_effect
    def hello(app):
        pass

    assert config.custom_effects == [hello]


def test_linemod_config():
    config = LineModeConfig()

    assert config.process == []

    @config.register
    def what(file):
        pass

    assert config._process == [what]


def test_base_style_config():
    class Config(BaseStyleConfig):
        def __init__(self) -> None:
            self.bar = "#ffffff"
            self.header = "#000000"

    config = Config()
    assert dict(config) == {"bar": "#ffffff", "header": "#000000"}

    config.clear()
    assert dict(config) == {"bar": "", "header": ""}


def test_style_config():
    style_config = StyleConfig()

    @style_config.register("hello")
    class Hello(BaseStyleConfig):
        def __init__(self) -> None:
            self.file_color = "#ffffff"

    assert hasattr(style_config, "hello") == True
    assert dict(style_config)["hello.file_color"] == "#ffffff"


def test_kb_config_map(mocker: MockerFixture):
    kb = KBConfig()
    with pytest.raises(ClientError):
        kb.map(action="hello", keys="c-c")
    kb.map(action="exit", keys="c-c")

    def kb1(app):
        pass

    def kb2(app):
        pass

    kb.map(action=kb1, keys=Keys.ControlA)
    kb.map(action=kb2, keys=Keys.ControlB)
    kb.map(action=kb1, keys=Keys.ControlC)
    assert kb.custom_kb_maps == {
        KBMode.normal: {
            str(kb1): [
                {"keys": Keys.ControlA, "filter": mocker.ANY, "eager": False},
                {"keys": Keys.ControlC, "filter": mocker.ANY, "eager": False},
            ],
            str(kb2): [
                {"keys": Keys.ControlB, "filter": mocker.ANY, "eager": False},
            ],
        },
        KBMode.command: {},
    }
    assert kb.custom_kb_lookup == {
        KBMode.normal: {str(kb1): kb1, str(kb2): kb2},
        KBMode.command: {},
    }


def test_kb_config_unmap(mocker: MockerFixture):
    kb = KBConfig()
    kb.unmap("exit")
    assert kb.kb_maps[KBMode.normal].get("exit", False) == False

    def kb1(app):
        pass

    kb.map(action=kb1, keys="c-c")
    assert kb.custom_kb_lookup[KBMode.normal].get(str(kb1), False) == kb1
    kb.unmap(kb1)
    assert kb.custom_kb_lookup[KBMode.normal].get(str(kb1), False) == False
