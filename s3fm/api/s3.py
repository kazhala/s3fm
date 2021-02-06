"""Module contains the S3 class to access s3."""
import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from typing import List

import boto3
from mypy_boto3_s3 import Client


class S3:
    """Class to provide access and interacte with AWS s3.

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

    async def get_buckets(self) -> List[str]:
        """Async wrapper to list all buckets."""
        with ProcessPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, self.list_buckets)
            return result

    def list_buckets(self) -> List[str]:
        """List all buckets in the selected profile and region."""
        result = self.client.list_buckets()
        return [bucket["Name"] for bucket in result["Buckets"]]

    @property
    def client(self) -> Client:
        """Retrieve boto3 client."""
        client = boto3.client("s3")
        return client
