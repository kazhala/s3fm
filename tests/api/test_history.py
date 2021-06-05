import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import PropertyMock

import pytest
from pytest_mock.plugin import MockerFixture

from s3fm.api.history import Directory, History


@pytest.fixture
def hist_file():
    with tempfile.TemporaryDirectory() as tempdir:
        dst = Path(tempdir).joinpath("history.json")
        shutil.copy(
            src=Path(__file__).resolve().parent.joinpath("../data/fs_history.json"),
            dst=dst,
        )
        yield dst


@pytest.mark.asyncio
async def test_read(mocker: MockerFixture, hist_file):
    mocked_hist = mocker.patch.object(History, "hist_file", new_callable=PropertyMock)
    mocked_hist.return_value = hist_file

    history = History()
    await history.read()
    assert history._left_index == 2
    assert history._right_index == 3
    assert history._left_path == "/home/dir1/dir2/python/s3fm"
    assert isinstance(history._directory, Directory)


@pytest.mark.asyncio
async def test_write(mocker: MockerFixture, hist_file):
    mocked_hist = mocker.patch.object(History, "hist_file", new_callable=PropertyMock)
    mocked_hist.return_value = hist_file

    history = History()
    history._left_index = 100
    history.write()
    history._left_index = 0
    await history.read()
    assert history._left_index == 100
