"""
shared/storage/base.py — Abstract Storage Provider.

Purpose:
    Defines a generic interface for object storage (S3, GCS, Local).
"""

from abc import ABC, abstractmethod

class StorageProvider(ABC):
    """Interface for object storage operations."""

    @abstractmethod
    async def download_file(self, bucket: str, key: str, local_path: str) -> None:
        """Download an object to a local file path."""
        pass

    @abstractmethod
    async def upload_file(self, local_path: str, bucket: str, key: str) -> str:
        """Upload a local file to storage. Returns the public/internal URL."""
        pass

    @abstractmethod
    async def get_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Generate a temporary access URL."""
        pass

    @abstractmethod
    async def copy_file(self, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str) -> None:
        """Copy a file within or across buckets."""
        pass

    @abstractmethod
    async def delete_file(self, bucket: str, key: str) -> None:
        """Delete an object from storage."""
        pass
