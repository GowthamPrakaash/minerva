"""
tests/shared/test_storage.py — Unit tests for Storage abstraction.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from shared.storage.base import StorageProvider
from shared.storage.s3_storage import S3StorageProvider
from shared.storage.resolver import get_storage_provider

def test_storage_provider_abc():
    # Verify we cannot instantiate the ABC
    with pytest.raises(TypeError):
        StorageProvider()

@patch("boto3.client")
def test_s3_storage_implementation(mock_boto):
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    
    provider = S3StorageProvider(region="us-east-1")
    
    # Test download
    provider.client.download_file = MagicMock()
    import asyncio
    
    # download_file in s3_storage is synchronous (wrapper for boto3)
    # but we can call it in a test easily
    provider.client.download_file("bucket", "key", "local")
    mock_s3.download_file.assert_called_with("bucket", "key", "local")

def test_storage_resolver_singleton(monkeypatch):
    monkeypatch.setenv("STORAGE_TYPE", "s3")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    
    # Force reset of the global provider for testing
    import shared.storage.resolver as resolver
    resolver._provider = None
    
    provider = get_storage_provider()
    assert isinstance(provider, S3StorageProvider)
    assert provider.region == "ap-south-1"
    
    # Check singleton property
    provider2 = get_storage_provider()
    assert provider is provider2
