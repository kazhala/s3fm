"""Module contains the api class to access/interact with s3."""
from pathlib import Path
from typing import TYPE_CHECKING, List

import boto3
from mypy_boto3_s3.type_defs import BucketTypeDef

from s3fm.api.file import File
from s3fm.id import FileType
from s3fm.utils import transform_async

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3:
    """Class to provide access and interact with AWS s3.

    Args:
        bucket: Set the bucket.
        path: Set s3 path
    """

    def __init__(self, bucket: str = None, path: str = None) -> None:
        self._bucket = bucket or ""
        self._path = path or ""
        self._region = "ap-southeast-2"
        self._profile = "default"

    @transform_async
    def _list_buckets(self) -> List[BucketTypeDef]:
        """List all buckets in the selected profile and region."""
        return self.client.list_buckets()["Buckets"]

    async def get_buckets(self) -> List[File]:
        """Async wrapper to list all buckets.

        Retrieve a list of buckets under :obj:`concurrent.futures.ProcessPoolExecutor`.

        Returns:
            A list of :class:`~s3fm.id.File`.

        Examples:
            >>> import asyncio
            >>> from s3fm.api.s3 import S3
            >>> async def main():
            ...     s3 = S3()
            ...     files = await s3.get_buckets()
            >>> asyncio.run(main())
        """
        result = await self._list_buckets()
        return [
            File(
                name="%s/" % bucket["Name"],
                type=FileType.bucket,
                info="h",
                hidden=bucket["Name"].startswith("."),
                index=index,
            )
            for index, bucket in enumerate(result)
        ]

    @property
    def client(self) -> "S3Client":
        """S3Client: AWS boto3 client."""
        session = boto3.Session(region_name=self._region, profile_name=self._profile)
        client = session.client("s3")
        return client

    @property
    def uri(self) -> str:
        """str: Current s3 uri."""
        if not self._bucket:
            return "s3://"
        return "s3://%s" % str(Path(self._bucket).joinpath(self._path))

    @property
    def path(self) -> str:
        """str: S3 filepath."""
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        self._path = value
