"""
ingestion/pipeline/embedder.py — Text embedding generation.

Purpose:
    Generates vector embeddings for document chunks using a sentence
    transformer model.

Model:
    Default: all-MiniLM-L6-v2 (configurable per tenant via client_configs)

Methods:
    embed(chunks: list[str]) → numpy.ndarray

Notes:
    - Embeddings are normalised for cosine similarity (inner product with FAISS).
    - The embedding model is loaded as a singleton — shared across invocations.
"""

from __future__ import annotations

import numpy as np

from shared.exceptions.pipeline_exceptions import IngestionError
from shared.utils.logging import get_logger

logger = get_logger("ingestion.pipeline.embedder")

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

# Singleton cache: model_name → TextEmbedding instance
_model_cache: dict[str, object] = {}


def _get_model(model_name: str):
    """Load (or retrieve from cache) a FastEmbed TextEmbedding model."""
    if model_name in _model_cache:
        return _model_cache[model_name]

    try:
        from fastembed import TextEmbedding  # type: ignore
    except ImportError as exc:
        raise IngestionError(
            "embed",
            "fastembed is not installed. "
            "Run: pip install fastembed",
        ) from exc

    # FastEmbed uses a slightly different name for the same model if it's from sentence-transformers
    # Mapping for common ones:
    if model_name == "all-MiniLM-L6-v2":
        fastembed_name = "sentence-transformers/all-MiniLM-L6-v2"
    else:
        fastembed_name = model_name

    logger.info(f"Loading FastEmbed model: {fastembed_name}")
    model = TextEmbedding(model_name=fastembed_name)
    _model_cache[model_name] = model
    logger.info(f"FastEmbed model '{fastembed_name}' loaded and cached.")
    return model


def embed(
    chunks: list[str],
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 64,
) -> np.ndarray:
    """
    Generate L2-normalised embeddings for a list of text strings using FastEmbed.

    Args:
        chunks:     List of text strings to embed.
        model_name: Model identifier (defaults to all-MiniLM-L6-v2).
        batch_size: Number of chunks processed in iterative passes.

    Returns:
        float32 numpy array of shape (len(chunks), embedding_dim).
        Vectors are L2-normalised for use with FAISS inner product search.

    Raises:
        IngestionError: If fastembed is missing or encoding fails.
    """
    if not chunks:
        raise ValueError("embed() received an empty chunks list.")

    model = _get_model(model_name)

    logger.info(f"Embedding {len(chunks)} chunks with FastEmbed model '{model_name}'")
    try:
        # fastembed.embed returns a generator
        embeddings_gen = model.embed(
            chunks,
            batch_size=batch_size,
        )
        # Convert to numpy and ensure float32
        embeddings = np.array(list(embeddings_gen)).astype(np.float32)
        
        # FastEmbed might already normalize, but we ensure it for safety
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Handle zero norms (unlikely for text, but good for robustness)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms
        
    except Exception as exc:
        raise IngestionError("embed", f"FastEmbed embedding failed: {exc}") from exc

    logger.info(f"Generated embeddings: shape={embeddings.shape}")
    return embeddings
