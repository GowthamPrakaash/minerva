import pytest
import os
import shutil
import tempfile
from shared.storage.local_storage import LocalStorageProvider

@pytest.fixture
def local_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        provider = LocalStorageProvider(tmpdir)
        yield provider

@pytest.mark.asyncio
async def test_upload_download(local_storage):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"hello world")
        source_path = f.name
    
    try:
        # Upload
        await local_storage.upload_file(source_path, "test-bucket", "test-key.txt")
        
        # Verify file exists in local storage
        target_path = os.path.join(local_storage.base_path, "test-bucket", "test-key.txt")
        assert os.path.exists(target_path)
        with open(target_path, "rb") as f:
            assert f.read() == b"hello world"
            
        # Download
        with tempfile.NamedTemporaryFile(delete=False) as f2:
            dest_path = f2.name
            
        await local_storage.download_file("test-bucket", "test-key.txt", dest_path)
        with open(dest_path, "rb") as f:
            assert f.read() == b"hello world"
            
    finally:
        if os.path.exists(source_path): os.remove(source_path)
        if os.path.exists(dest_path): os.remove(dest_path)

@pytest.mark.asyncio
async def test_copy_file(local_storage):
    # Setup source
    bucket = "test-bucket"
    source_key = "source.txt"
    dest_key = "dest.txt"
    
    source_abs = os.path.join(local_storage.base_path, bucket, source_key)
    os.makedirs(os.path.dirname(source_abs), exist_ok=True)
    with open(source_abs, "w") as f:
        f.write("copy me")
        
    # Copy
    await local_storage.copy_file(bucket, source_key, bucket, dest_key)
    
    # Verify
    dest_abs = os.path.join(local_storage.base_path, bucket, dest_key)
    assert os.path.exists(dest_abs)
    with open(dest_abs, "r") as f:
        assert f.read() == "copy me"

@pytest.mark.asyncio
async def test_delete_file(local_storage):
    bucket = "test-bucket"
    key = "delete-me.txt"
    
    abs_path = os.path.join(local_storage.base_path, bucket, key)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w") as f:
        f.write("content")
        
    await local_storage.delete_file(bucket, key)
    assert not os.path.exists(abs_path)
