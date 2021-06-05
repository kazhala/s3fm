import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest.mock import ANY, PropertyMock

import boto3
import pytest
from botocore.stub import Stubber
from pytest_mock.plugin import MockerFixture

from s3fm.api.fs import FS, S3, File
from s3fm.enums import FileType
from s3fm.exceptions import Notification


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
    yield ["2.txt", "3.txt", "1.txt", ".6.txt"]


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

        assert len(await fs.cd()) == 7

    @pytest.mark.asyncio
    async def test_cd_override(self, fs: FS):
        await fs.cd(Path.home(), override=True)
        assert fs.path == Path.home().resolve()

    @pytest.mark.asyncio
    async def test_cd_file(self, fs: FS):
        with pytest.raises(Notification):
            await fs.cd(Path("asdfasfasdfasfas"))

    @pytest.mark.asyncio
    async def test_get_paths(self, fs: FS, test_dirs, test_files):
        assert await fs.get_paths() == [
            File(name="..", type=FileType.dir, info="", hidden=False, index=0, raw=ANY),
            File(
                name="4xx/", type=FileType.dir, info="", hidden=False, index=1, raw=ANY
            ),
            File(
                name="5xx/", type=FileType.dir, info="", hidden=False, index=2, raw=ANY
            ),
            File(
                name=".6.txt",
                type=FileType.file,
                info="0 B",
                hidden=True,
                index=3,
                raw=ANY,
            ),
            File(
                name="1.txt",
                type=FileType.file,
                info="0 B",
                hidden=False,
                index=4,
                raw=ANY,
            ),
            File(
                name="2.txt",
                type=FileType.file,
                info="0 B",
                hidden=False,
                index=5,
                raw=ANY,
            ),
            File(
                name="3.txt",
                type=FileType.file,
                info="0 B",
                hidden=False,
                index=6,
                raw=ANY,
            ),
        ]


class TestS3:
    @pytest.mark.asyncio
    async def test_get_buckets(self, mocker: MockerFixture):
        with Path(__file__).resolve().parent.joinpath(
            "../data/s3_list_buckets.json"
        ).open("r") as file:
            response = json.load(file)

        curr_time = datetime.now()
        for bucket in response["Buckets"]:
            bucket["CreationDate"] = curr_time

        patched_s3 = mocker.patch.object(S3, "_list_buckets")
        patched_s3.return_value = response

        s3 = S3()
        assert await s3._get_buckets() == [
            File(
                name="bucket1/",
                type=FileType.bucket,
                info=str(curr_time),
                hidden=False,
                index=0,
                raw={"Name": "bucket1", "CreationDate": curr_time},
            ),
            File(
                name="bucket2/",
                type=FileType.bucket,
                info=str(curr_time),
                hidden=False,
                index=1,
                raw={"Name": "bucket2", "CreationDate": curr_time},
            ),
            File(
                name="bucket3/",
                type=FileType.bucket,
                info=str(curr_time),
                hidden=False,
                index=2,
                raw={"Name": "bucket3", "CreationDate": curr_time},
            ),
            File(
                name="bucket4/",
                type=FileType.bucket,
                info=str(curr_time),
                hidden=False,
                index=3,
                raw={"Name": "bucket4", "CreationDate": curr_time},
            ),
            File(
                name="bucket5/",
                type=FileType.bucket,
                info=str(curr_time),
                hidden=False,
                index=4,
                raw={"Name": "bucket5", "CreationDate": curr_time},
            ),
        ]
