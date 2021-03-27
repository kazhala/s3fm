"""Module contains the api class to access/interact with s3."""
from typing import TYPE_CHECKING, List

import boto3
from mypy_boto3_s3.type_defs import BucketTypeDef, ObjectTypeDef

from s3fm.api.file import File
from s3fm.id import FileType
from s3fm.utils import transform_async

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3:
    """Class to provide access and interact with AWS s3."""

    def __init__(self) -> None:
        self._path = ""
        self._region = "ap-southeast-2"
        self._profile = "default"

    @transform_async
    def _list_buckets(self) -> List[BucketTypeDef]:
        """List all buckets in the selected profile and region."""
        return self.client.list_buckets()["Buckets"]

    @transform_async
    def _list_objects(self, full_data: bool = False) -> List[ObjectTypeDef]:
        """List all objects within selected bucket."""
        return self.client.list_objects_v2(
            Bucket=self.bucket_name, Delimiter="/", Prefix=self.bucket_path
        )["Contents"]

    async def _get_buckets(self) -> List[File]:
        """Async wrapper to list all buckets.

        Returns:
            A list of :class:`~s3fm.id.File`.
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

    async def _get_objects(self, offset: int = 0) -> List[File]:
        """Async wrapper to list all objects in bucket.

        Returns:
            A list of :class:`~s3fm.id.File`.
        """
        result = await self._list_objects()
        return [
            File(
                name=s3_obj["Key"],
                type=FileType.dir if s3_obj["Key"].endswith("/") else FileType.file,
                info=str(s3_obj["LastModified"]),
                hidden=s3_obj["Key"].startswith("."),
                index=index + offset,
            )
            for index, s3_obj in enumerate(result)
        ]

    async def get_paths(self) -> List[File]:
        """Async wrapper to retrieve list of s3 buckets or objects.

        Retrieve a list of buckets to display or a list of s3 objects
        to display if the bucket is already choosen.

        Returns:
            A list of :class:`~s3fm.id.File`.

        Examples:
            >>> import asyncio
            >>> from s3fm.api.s3 import S3
            >>> async def main():
            ...     s3 = S3()
            ...     files = await s3.get_paths()
            >>> asyncio.run(main())
        """
        if not self._path:
            return await self._get_buckets()
        else:
            return [
                File(name="..", type=FileType.dir, hidden=False, index=0, info="")
            ] + await self._get_objects(offset=1)

    @property
    def client(self) -> "S3Client":
        """S3Client: AWS boto3 client."""
        session = boto3.Session(region_name=self._region, profile_name=self._profile)
        client = session.client("s3")
        return client

    @property
    def uri(self) -> str:
        """str: Current s3 uri."""
        return "s3://%s" % self._path

    @property
    def path(self) -> str:
        """str: S3 filepath."""
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    @property
    def bucket_name(self) -> str:
        """str: Name of the selected bucket."""
        if not self._path:
            return ""
        return self._path.split("/")[0]

    @property
    def bucket_path(self) -> str:
        """str: Current s3 path."""
        return self._path.replace(self.bucket_name, "")
