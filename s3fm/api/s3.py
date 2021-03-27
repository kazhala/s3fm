"""Module contains the api class to access/interact with s3."""
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

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
        self._path = Path("")
        self._region = "ap-southeast-2"
        self._profile = "default"

    @transform_async
    def _list_buckets(self) -> List[BucketTypeDef]:
        """List all buckets in the selected profile and region."""
        return self.client.list_buckets()["Buckets"]

    @transform_async
    def _list_objects(self, full_data: bool = False) -> List[Union[str, ObjectTypeDef]]:
        """List all objects within selected bucket."""
        result = []
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix="%s/" % self.bucket_path if self.bucket_path else "",
            Delimiter="/",
        )
        for prefix in response.get("CommonPrefixes", []):
            result.append(prefix["Prefix"])
        for s3_obj in response.get("Contents", []):
            result.append(s3_obj)
        return result

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
                info=str(bucket["CreationDate"]),
                hidden=bucket["Name"].startswith("."),
                index=index,
                raw=bucket,
            )
            for index, bucket in enumerate(result)
        ]

    async def _get_objects(self, offset: int = 0) -> List[File]:
        """Async wrapper to list all objects in bucket.

        Returns:
            A list of :class:`~s3fm.id.File`.
        """
        response = await self._list_objects()
        result = []
        for index, s3_obj in enumerate(response):
            if isinstance(s3_obj, str):
                result.append(
                    File(
                        name=s3_obj,
                        type=FileType.dir,
                        info="",
                        hidden=s3_obj.startswith("."),
                        index=index + offset,
                        raw=None,
                    )
                )
            else:
                result.append(
                    File(
                        name=Path(s3_obj["Key"]).name,
                        type=FileType.dir
                        if s3_obj["Key"].endswith("/")
                        else FileType.file,
                        info=str(s3_obj["LastModified"]),
                        hidden=s3_obj["Key"].startswith("."),
                        index=index + offset,
                        raw=s3_obj,
                    )
                )
        return result

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
        if str(self._path) == ".":
            return await self._get_buckets()
        else:
            return [
                File(
                    name="..",
                    type=FileType.dir,
                    hidden=False,
                    index=0,
                    info="",
                    raw=None,
                )
            ] + await self._get_objects(offset=1)

    async def cd(self, path: str = "", override: bool = False) -> List[File]:
        """Update s3 path or select a bucket if not selected.

        Args:
            path: A :obj:`str` representing target path/bucket.
                If not provided, navigate to current path parent.
            override: Change directory to a absolute new path without
                any consideration of the current path.

        Returns:
            A list of files in the new directory.
        """
        if not path or path == "..":
            self._path = self._path.parent
        else:
            if override:
                self._path = Path(path)
            else:
                self._path = self._path.joinpath(path)
        # TODO: permission handling
        return await self.get_paths()

    @property
    def client(self) -> "S3Client":
        """S3Client: AWS boto3 client."""
        session = boto3.Session(region_name=self._region, profile_name=self._profile)
        client = session.client("s3")
        return client

    @property
    def uri(self) -> str:
        """str: Current s3 uri."""
        return "s3://%s" % ("" if str(self._path) == "." else self._path)

    @property
    def path(self) -> Path:
        """str: S3 filepath."""
        return self._path

    @path.setter
    def path(self, value: Path) -> None:
        self._path = value

    @property
    def bucket_name(self) -> str:
        """str: Name of the selected bucket."""
        if str(self._path) == ".":
            return ""
        return self._path.parts[0]

    @property
    def bucket_path(self) -> str:
        """str: Current s3 path."""
        if str(self._path) == ".":
            return ""
        return "/".join(self._path.parts[1:])
