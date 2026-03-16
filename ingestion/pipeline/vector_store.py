"""
ingestion/pipeline/vector_store.py — Vector index management.

Purpose:
    Creates, updates, and archives FAISS vector indexes for RAG retrieval.
    Abstracted via StorageProvider to remain cloud-agnostic.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

import faiss  # type: ignore
import numpy as np

from shared.exceptions.pipeline_exceptions import IngestionError
from shared.utils.logging import get_logger
from shared.storage.resolver import get_storage_provider

logger = get_logger("ingestion.pipeline.vector_store")

_STORAGE_BUCKET = os.environ.get("S3_BUCKET", "minerva-documents")
_INDEX_FILENAME = "faiss.index"
_META_FILENAME = "chunk_metadata.json"


def build_index(embeddings: np.ndarray, metadata: list[dict]) -> faiss.Index:
    """Build a FAISS inner-product index from L2-normalised embeddings."""
    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise IngestionError("vector_store", "Embeddings array must be 2-D and non-empty.")
    if len(metadata) != embeddings.shape[0]:
        raise IngestionError(
            "vector_store",
            f"metadata length ({len(metadata)}) != embeddings rows ({embeddings.shape[0]})",
        )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    logger.info(f"Built FAISS index: {index.ntotal} vectors, dim={dim}")
    return index


async def save_index(
    index: faiss.Index,
    metadata: list[dict],
    business_id: str,
    job_id: str,
) -> str:
    """Serialise and upload the FAISS index + metadata to storage."""
    prefix = _active_index_prefix(business_id)
    storage = get_storage_provider()

    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, _INDEX_FILENAME)
        meta_path = os.path.join(tmpdir, _META_FILENAME)

        faiss.write_index(index, index_path)
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh)

        await storage.upload_file(index_path, _STORAGE_BUCKET, f"{prefix}/{_INDEX_FILENAME}")
        await storage.upload_file(meta_path, _STORAGE_BUCKET, f"{prefix}/{_META_FILENAME}")

    storage_path = f"{_STORAGE_BUCKET}/{prefix}"
    logger.info(f"Saved vector index to {storage_path} (job_id={job_id})")
    return storage_path


async def archive_previous_index(business_id: str, job_id: str) -> None:
    """Archive current active index via StorageProvider."""
    storage = get_storage_provider()
    active_prefix = _active_index_prefix(business_id)
    archive_prefix = _archive_index_prefix(business_id, job_id)

    for filename in (_INDEX_FILENAME, _META_FILENAME):
        src_key = f"{active_prefix}/{filename}"
        dst_key = f"{archive_prefix}/{filename}"
        try:
            await storage.copy_file(
                src_bucket=_STORAGE_BUCKET,
                src_key=src_key,
                dst_bucket=_STORAGE_BUCKET,
                dst_key=dst_key,
            )
            logger.info(f"Archived {src_key} → {dst_key}")
        except Exception as exc:
            # We check for NoSuchKey in implementation or just log info if it's missing
            logger.info(f"No existing index to archive at {src_key} or archival failed: {exc}")


async def load_index(business_id: str) -> tuple[faiss.Index, list[dict]]:
    """Download and deserialise the active FAISS index."""
    prefix = _active_index_prefix(business_id)
    storage = get_storage_provider()

    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, _INDEX_FILENAME)
        meta_path = os.path.join(tmpdir, _META_FILENAME)

        try:
            await storage.download_file(_STORAGE_BUCKET, f"{prefix}/{_INDEX_FILENAME}", index_path)
            await storage.download_file(_STORAGE_BUCKET, f"{prefix}/{_META_FILENAME}", meta_path)
        except Exception as exc:
            raise IngestionError(
                "vector_store",
                f"Failed to download index for business {business_id}: {exc}",
            ) from exc

        index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as fh:
            metadata = json.load(fh)

    logger.info(f"Loaded FAISS index for business {business_id}: {index.ntotal} vectors")
    return index, metadata


def _active_index_prefix(business_id: str) -> str:
    return f"businesses/{business_id}/index"


def _archive_index_prefix(business_id: str, job_id: str) -> str:
    return f"businesses/{business_id}/archives/{job_id}"
