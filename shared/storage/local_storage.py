"""
shared/storage/local_storage.py — Local Disk implementation of StorageProvider.
"""

import os
import shutil
import aiofiles
from .base import StorageProvider
from shared.utils.logging import get_logger

logger = get_logger("shared.storage.local")

class LocalStorageProvider(StorageProvider):
    """Local file system specific storage implementation."""

    def __init__(self, base_path: str = "/tmp/minerva_storage"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
            logger.info(f"LocalStorage: Created base directory at {self.base_path}")

    def _get_full_path(self, bucket: str, key: str) -> str:
        full_dir = os.path.join(self.base_path, bucket, os.path.dirname(key))
        os.makedirs(full_dir, exist_ok=True)
        return os.path.join(self.base_path, bucket, key)

    async def download_file(self, bucket: str, key: str, local_path: str) -> None:
        src = self._get_full_path(bucket, key)
        if not os.path.exists(src):
            raise FileNotFoundError(f"LocalStorage: File not found at {src}")
        
        logger.debug(f"LocalStorage: Copying {src} -> {local_path}")
        shutil.copy2(src, local_path)

    async def upload_file(self, local_path: str, bucket: str, key: str) -> str:
        dst = self._get_full_path(bucket, key)
        logger.debug(f"LocalStorage: Copying {local_path} -> {dst}")
        shutil.copy2(local_path, dst)
        return f"local://{bucket}/{key}"

    async def get_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        # For local testing, just return the file path
        return f"file://{self._get_full_path(bucket, key)}"

    async def copy_file(self, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str) -> None:
        src = self._get_full_path(src_bucket, src_key)
        dst = self._get_full_path(dst_bucket, dst_key)
        if not os.path.exists(src):
            raise FileNotFoundError(f"LocalStorage: Source file not found at {src}")
        
        logger.debug(f"LocalStorage: copying {src} -> {dst}")
        shutil.copy2(src, dst)

    async def delete_file(self, bucket: str, key: str) -> None:
        path = self._get_full_path(bucket, key)
        if os.path.exists(path):
            logger.debug(f"LocalStorage: Deleting {path}")
            os.remove(path)
        else:
            logger.warning(f"LocalStorage: File not found for deletion: {path}")
