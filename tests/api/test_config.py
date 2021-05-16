import pytest

from s3fm.api.config import AppConfig, LineModeConfig


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
