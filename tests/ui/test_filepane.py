from pathlib import Path

import pytest
from pytest_mock.plugin import MockerFixture

from s3fm.app import App
from s3fm.enums import PaneMode
from s3fm.ui.filepane import FilePane, file_action, hist_dir, spin_spinner


@pytest.mark.asyncio
async def test_hist_dir_no_cd(app: App):
    @hist_dir
    async def no_cd(filepane):
        pass

    assert app._left_pane._history._directory == {}
    await no_cd(app._left_pane)
    assert app._left_pane._history._directory == {".": 0}

    app._right_pane._history._directory = {".": 12}
    await no_cd(app._right_pane)
    assert app._right_pane._history._directory == {".": 12}


@pytest.mark.asyncio
async def test_hist_dir_cd(app: App):
    @hist_dir
    async def cd(filepane: FilePane):
        filepane._fs.path = Path().absolute().root

    curr_path = app._left_pane._fs.path
    app._left_pane._mode = PaneMode.fs
    app._left_pane.selected_file_index = 1
    assert app._left_pane._history._directory == {}
    await cd(app._left_pane)
    assert app._left_pane._history._directory == {str(curr_path): 1}

    curr_path = app._right_pane._fs.path
    app._right_pane._mode = PaneMode.fs
    app._right_pane._history._directory = {".": 12}
    await cd(app._right_pane)
    assert app._left_pane._history._directory == {".": 12, str(curr_path): 0}


@pytest.mark.asyncio
async def test_spin_spinner(app: App, mocker: MockerFixture):
    @spin_spinner
    async def spin(filepane: FilePane):
        assert filepane.loading == True

    await spin(app._left_pane)
    assert app._left_pane.loading == False


@pytest.mark.asyncio
async def test_file_action(app: App, mocker: MockerFixture):
    @file_action
    async def file_operation(filepane: FilePane):
        assert True == False

    await file_operation(app._left_pane)

    mocked_selection = mocker.patch.object(FilePane, "current_selection")
    mocked_selection.return_value = None
    with pytest.raises(AssertionError):
        await file_operation(app._left_pane)
