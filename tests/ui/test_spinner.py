import pytest
from pytest_mock.plugin import MockerFixture

from s3fm.app import App


def test_get_text(app: App):
    assert app._left_pane.spinner._get_text() == [
        ("class:spinner.pattern", "|"),
        ("class:spinner.text", " Loading"),
    ]


@pytest.mark.asyncio
async def test_start(app: App, mocker: MockerFixture):
    def hello():
        app._left_pane.loading = False

    app._left_pane.spinner._redraw = hello
    await app._left_pane.spinner.start()
    assert app._left_pane.spinner._spinning == False

    app._left_pane.spinner._spinning = True
    await app._left_pane.spinner.start()
    assert app._left_pane.spinner._spinning == True
