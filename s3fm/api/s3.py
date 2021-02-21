"""Module contains the main api class to access s3."""
import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from typing import TYPE_CHECKING, List

import boto3
from mypy_boto3_s3.type_defs import BucketTypeDef

from s3fm.base import CHOICES, ChoiceType

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3:
    """Class to provide access and interact with AWS s3.

    :param bucket: bucket name
    :type bucket: str
    :param path: s3 object path
    :type path: str
    """

    def __init__(self, bucket: str = None, path: str = None) -> None:
        """Initialise required base properties to create s3 client."""
        self._bucket = bucket or ""
        self._path = path or ""
        self._region = "ap-southeast-2"
        self._profile = "default"

    async def get_buckets(self) -> List[CHOICES]:
        """Async wrapper to list all buckets."""
        with ProcessPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, self.list_buckets)
            return [
                {"Name": bucket["Name"], "Type": ChoiceType.s3_bucket}
                for bucket in result
            ]

    def list_buckets(self) -> List[BucketTypeDef]:
        """List all buckets in the selected profile and region."""
        return self.client.list_buckets()["Buckets"]

    @property
    def client(self) -> "S3Client":
        """Retrieve boto3 client."""
        session = boto3.Session(region_name=self._region, profile_name=self._profile)
        client = session.client("s3")
        return client
