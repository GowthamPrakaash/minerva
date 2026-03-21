"""
shared/storage/resolver.py — Resolves the active storage provider.
"""

import os
from .base import StorageProvider
from .s3_storage import S3StorageProvider
from .local_storage import LocalStorageProvider

_provider: StorageProvider | None = None

def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider singleton."""
    global _provider
    if _provider is None:
        storage_type = os.environ.get("STORAGE_TYPE", "s3").lower()
        
        if storage_type == "s3":
            region = os.environ.get("AWS_REGION", "us-east-1")
            _provider = S3StorageProvider(region=region)
        elif storage_type == "local":
            base_path = os.environ.get("LOCAL_STORAGE_PATH", "/home/parrot/dev/projects/minerva/storage")
            _provider = LocalStorageProvider(base_path=base_path)
        else:
            raise ValueError(f"Unknown STORAGE_TYPE: {storage_type}")
            
    return _provider
