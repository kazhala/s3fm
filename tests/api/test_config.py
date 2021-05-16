import pytest

from s3fm.api.config import AppConfig, BaseStyleConfig, LineModeConfig, StyleConfig


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
