"""
core/pipelines/components/vector_manager.py — In-memory index cache for Core.

Purpose:
    Handles caching of FAISS indexes. Downloads are abstracted 
    via StorageProvider to remain cloud-agnostic.
"""

import os
import faiss
import json
import tempfile
from typing import Optional
from shared.utils.logging import get_logger
from shared.storage.resolver import get_storage_provider

logger = get_logger("core.pipelines.components.vector_manager")

_STORAGE_BUCKET = os.environ.get("S3_BUCKET", "minerva-documents")
_INDEX_CACHE: dict[str, tuple[faiss.Index, list[dict]]] = {}


async def get_index(business_id: str) -> tuple[faiss.Index, list[dict]]:
    """
    Retrieve the FAISS index and metadata for a business.
    Downloads via StorageProvider if not in local cache.
    """
    if business_id in _INDEX_CACHE:
        return _INDEX_CACHE[business_id]

    logger.info(f"VectorManager: Loading index for business {business_id}.")
    
    storage = get_storage_provider()
    prefix = f"businesses/{business_id}/index"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "faiss.index")
        meta_path = os.path.join(tmpdir, "chunk_metadata.json")

        try:
            # Cloud agnostic download
            await storage.download_file(_STORAGE_BUCKET, f"{prefix}/faiss.index", index_path)
            await storage.download_file(_STORAGE_BUCKET, f"{prefix}/chunk_metadata.json", meta_path)
        except Exception as exc:
            logger.error(f"VectorManager: Failed to download index for {business_id}: {exc}")
            raise

        # FAISS is local logic (not cloud specific)
        index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    _INDEX_CACHE[business_id] = (index, metadata)
    logger.info(f"VectorManager: Index loaded for {business_id}. Total vectors: {index.ntotal}")
    return index, metadata


def invalidate_index(business_id: str):
    """Remove a business index from the local cache."""
    if business_id in _INDEX_CACHE:
        del _INDEX_CACHE[business_id]
        logger.info(f"VectorManager: Invalidated index for business {business_id}")
