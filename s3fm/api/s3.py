"""Module contains the api class to access/interact with s3."""
from pathlib import Path
from typing import TYPE_CHECKING, List

import boto3

from s3fm.api.file import File
from s3fm.id import FileType
from s3fm.utils import human_readable_size, transform_async

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import (
        ListBucketsOutputTypeDef,
        ListObjectsV2OutputTypeDef,
    )


class S3:
    """Class to provide access and interact with AWS s3."""

    def __init__(self) -> None:
        self._path = Path("")
        self._region = "ap-southeast-2"
        self._profile = "default"

    @transform_async
    def _list_buckets(self) -> "ListBucketsOutputTypeDef":
        """List all buckets in the selected profile and region."""
        return self.client.list_buckets()

    @transform_async
    def _list_objects(self) -> "ListObjectsV2OutputTypeDef":
        """List all objects within selected bucket."""
        return self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix="%s/" % self.bucket_path if self.bucket_path else "",
            Delimiter="/",
        )

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
                info=str(bucket["CreationDate"].replace(tzinfo=None)),
                hidden=bucket["Name"].startswith("."),
                index=index,
                raw=bucket,
            )
            for index, bucket in enumerate(result.get("Buckets", []))
        ]

    async def _get_objects(self, offset: int = 0) -> List[File]:
        """Async wrapper to list all objects in bucket.

        Returns:
            A list of :class:`~s3fm.id.File`.
        """
        response = await self._list_objects()
        result = []
        for index, s3_obj in enumerate(response.get("CommonPrefixes", [])):
            result.append(
                File(
                    name="%s/" % Path(s3_obj["Prefix"]).name,
                    type=FileType.dir,
                    info="",
                    hidden=s3_obj["Prefix"].startswith("."),
                    index=index + offset,
                    raw=None,
                )
            )
        for index, s3_obj in enumerate(response.get("Contents", [])):
            result.append(
                File(
                    name=Path(s3_obj["Key"]).name,
                    type=FileType.dir if s3_obj["Key"].endswith("/") else FileType.file,
                    info=str(human_readable_size(s3_obj["Size"])),
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
