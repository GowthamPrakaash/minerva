"""
shared/storage/s3_storage.py — AWS S3 implementation of StorageProvider.
"""

import boto3
import aiobotocore
from botocore.exceptions import ClientError
from .base import StorageProvider
from shared.utils.logging import get_logger

logger = get_logger("shared.storage.s3")

class S3StorageProvider(StorageProvider):
    """S3 specific storage implementation."""

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        # In a high-performance async app, we'd use aiobotocore
        # But for simple downloads, standard boto3 in a threadpool or 
        # aiobotocore handles it better.
        self.client = boto3.client("s3", region_name=region)

    async def download_file(self, bucket: str, key: str, local_path: str) -> None:
        try:
            # Note: In a fully production async app, this would be wrapped 
            # in run_in_executor or use aiobotocore.
            self.client.download_file(bucket, key, local_path)
        except ClientError as e:
            logger.error(f"S3 Download Error: {e}")
            raise

    async def upload_file(self, local_path: str, bucket: str, key: str) -> str:
        try:
            self.client.upload_file(local_path, bucket, key)
            return f"s3://{bucket}/{key}"
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            raise

    async def get_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in
            )
        except ClientError as e:
            logger.error(f"S3 Presigned URL Error: {e}")
            raise

    async def copy_file(self, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str) -> None:
        try:
            self.client.copy_object(
                Bucket=dst_bucket,
                CopySource={"Bucket": src_bucket, "Key": src_key},
                Key=dst_key,
            )
        except ClientError as e:
            logger.error(f"S3 Copy Error: {e}")
            raise

    async def delete_file(self, bucket: str, key: str) -> None:
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
        except ClientError as e:
            logger.error(f"S3 Delete Error: {e}")
            raise
