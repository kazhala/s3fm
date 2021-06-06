from typing import NamedTuple

import pytest
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent, KeyProcessor
from pytest_mock.plugin import MockerFixture

from s3fm.api.kb import KB
from s3fm.app import App
from s3fm.enums import Direction, KBMode, LayoutMode
from s3fm.ui.filepane import FilePane


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
    kb._pane_set_action_multiplier(mocked_event)
    assert kb._action_multiplier == 0

    mocked_event = FakeEvent([FakeSequence("1")])
    kb._pane_set_action_multiplier(mocked_event)
    assert kb._action_multiplier == 1

    mocked_event = FakeEvent([FakeSequence("1")])
    kb._pane_set_action_multiplier(mocked_event)
    assert kb._action_multiplier == 11


def test_swap_pane(mocker: MockerFixture, kb):
    mocked_swap = mocker.patch.object(App, "pane_swap")

    kb._swap_pane(Direction.left)
    mocked_swap.assert_called_with(Direction.left, layout=LayoutMode.vertical)

    kb._swap_pane(Direction.down)
    mocked_swap.assert_called_with(Direction.down, layout=LayoutMode.horizontal)


def test_scroll_down(mocker: MockerFixture, kb):
    mocked_scorll = mocker.patch.object(FilePane, "scroll_down")

    kb._pane_scroll_down()
    mocked_scorll.assert_called_with(value=1, page=False, bottom=False)

    kb._action_multiplier = 11
    kb._pane_scroll_down(page=True, bottom=True)
    mocked_scorll.assert_called_with(value=11, page=True, bottom=True)


def test_scroll_up(mocker: MockerFixture, kb):
    mocked_scorll = mocker.patch.object(FilePane, "scroll_up")

    kb._pane_scroll_up()
    mocked_scorll.assert_called_with(value=1, page=False, top=False)

    kb._action_multiplier = 11
    kb._pane_scroll_up(page=True, top=True)
    mocked_scorll.assert_called_with(value=11, page=True, top=True)
