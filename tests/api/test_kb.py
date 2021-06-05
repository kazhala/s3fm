from typing import NamedTuple

import pytest
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent, KeyProcessor

from s3fm.api.kb import KB
from s3fm.app import App
from s3fm.enums import KBMode


@pytest.fixture
def kb(app: App):
    kb = KB(
        app=app,
        kb_maps={
            KBMode.normal: {"exit": [{"keys": "c-c"}]},
            KBMode.command: {"exit": [{"keys": "c-c"}]},
        },
        custom_kb_maps={KBMode.normal: {"hello": [{"keys": "j"}]}, KBMode.command: {}},
        custom_kb_lookup={KBMode.normal: {"hello": lambda: True}, KBMode.command: {}},
    )
    yield kb


def test_init(kb):
    assert isinstance(kb, KeyBindings)
    assert len(kb.bindings) == 13


def test_set_action_multiplier(kb):
    class FakeEvent(NamedTuple):
        key_sequence: list

    class FakeSequence(NamedTuple):
        key: str

    mocked_event = FakeEvent([FakeSequence("0")])
    kb._set_action_multiplier(mocked_event)
    assert kb._action_multiplier == 0

    mocked_event = FakeEvent([FakeSequence("1")])
    kb._set_action_multiplier(mocked_event)
    assert kb._action_multiplier == 1

    mocked_event = FakeEvent([FakeSequence("1")])
    kb._set_action_multiplier(mocked_event)
    assert kb._action_multiplier == 11
