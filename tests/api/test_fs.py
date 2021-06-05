import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from s3fm.api.fs import FS, File
from s3fm.enums import FileType
from s3fm.exceptions import Bug


@contextmanager
def chdir(path: Path):
    cwd = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(cwd)


@pytest.fixture
def test_files():
    yield ["2.txt", "3.txt", "1.txt"]


@pytest.fixture
def test_dirs():
    yield ["4xx", "5xx"]


@pytest.fixture
def fs(test_files, test_dirs):
    with tempfile.TemporaryDirectory() as tempdir:
        for file in test_files:
            with open("%s/%s" % (tempdir, file), "w") as out:
                out.write("")
        for directory in test_dirs:
            os.mkdir("%s/%s" % (tempdir, directory))
        fs = FS()
        fs.path = Path(tempdir)
        yield fs


class TestFS:
    @pytest.mark.asyncio
    async def test_list_files(self, fs: FS, test_dirs, test_files):
        result = list(sorted(test_dirs)) + list(sorted(test_files))
        assert await fs._list_files() == [fs.path.joinpath(path) for path in result]

    @pytest.mark.asyncio
    async def test_cd(self, fs: FS, test_dirs):
        cwd = fs.path
        assert await fs.cd(Path(test_dirs[0])) == [
            File(name="..", type=FileType.dir, info="", hidden=False, index=0, raw=None)
        ]
        assert fs.path == cwd.joinpath(test_dirs[0]).resolve()

        assert len(await fs.cd()) == 6

    @pytest.mark.asyncio
    async def test_cd_override(self, fs: FS):
        await fs.cd(Path.home(), override=True)
        assert fs.path == Path.home().resolve()

    @pytest.mark.asyncio
    async def test_cd_file(self, fs: FS):
        with pytest.raises(Bug):
            await fs.cd(Path("asdfasfasdfasfas"))
