import pytest

from s3fm.app import App
from s3fm.enums import ErrorType
from s3fm.exceptions import Bug, Notification


def test_get_title(app: App):
    app.set_error(Notification(message="hello", error_type=ErrorType.error))
    assert app._error_pane._get_title() == [("class:error.error", "ERROR")]
    app.set_error(Notification(message="hello", error_type=ErrorType.warning))
    assert app._error_pane._get_title() == [("class:error.warning", "WARNING")]
    app.set_error(Notification(message="hello", error_type=ErrorType.info))
    assert app._error_pane._get_title() == [("class:error.info", "INFO")]


def test_get_text(app: App):
    app.set_error(Notification(message="hello", error_type=ErrorType.error))
    assert app._error_pane._get_text() == [
        ("", "\n"),
        ("class:error.error", "hello"),
        ("", "\n"),
        ("", "\n"),
        ("class:error.instruction", "Press any key to continue ..."),
    ]

    app.set_error(Notification(message="hello", error_type=ErrorType.warning))
    assert app._error_pane._get_text() == [
        ("", "\n"),
        ("class:error.warning", "hello"),
        ("", "\n"),
        ("", "\n"),
        ("class:error.instruction", "Press any key to continue ..."),
    ]

    app.set_error(Notification(message="hello", error_type=ErrorType.info))
    assert app._error_pane._get_text() == [
        ("", "\n"),
        ("class:error.info", "hello"),
        ("", "\n"),
        ("", "\n"),
        ("class:error.instruction", "Press any key to continue ..."),
    ]


def test_bug():
    with pytest.raises(Bug):
        hello = Bug(message="hello")
        assert (
            hello._message
            == "hello\nSomething went wrong with s3fm, please report this behavior over at https://github.com/kazhala/s3fm/issues."
        )
        raise hello
