import inspect
import os

import pytest

from s3fm.utils import get_dimension, human_readable_size, transform_async


def test_get_dimension():
    os.environ["LINES"] = "10"
    os.environ["COLUMNS"] = "20"
    assert get_dimension() == (20, 10)
    assert get_dimension(offset=10) == (10, 0)


@pytest.mark.asyncio
async def test_transform_async():
    def hello_world1():
        return 1

    assert inspect.iscoroutinefunction(hello_world1) == False
    assert hello_world1() == 1

    @transform_async
    def hello_world2():
        return 1

    assert inspect.iscoroutinefunction(hello_world2) == True
    assert await hello_world2() == 1


def test_human_readable_size():
    assert human_readable_size(10) == "10 B"
    assert human_readable_size(1024) == "1.0 K"
    assert human_readable_size(8735823118) == "8.1 G"
    assert human_readable_size(9973588823118) == "9.1 T"
    assert human_readable_size(8009973588823118) == "7.1 P"
    assert human_readable_size(1234009973588823118) == "1.1 E"
