"""
shared/models/api_key.py — Tenant-scoped API key pair model.

Table: tenant_<slug>.api_keys

Fields:
    id, api_key, api_secret_hash, is_active

Business Rules:
    - API keys are scoped to a specific Business (not the Organization).
    - Maximum 2 active keys per business.
    - api_secret is stored as a bcrypt hash — the plaintext is never persisted.
    - The api_key resolves directly to a business_id at runtime, which determines
      the active tenant schema, FAISS index, and configuration.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ApiKey:
    """Represents a row in tenant_<slug>.api_keys."""

    id: uuid.UUID
    api_key: str                    # Public key (sent in auth requests)
    api_secret_hash: str            # bcrypt hash of the secret
    is_active: bool = True

    # Audit columns
    created_by: Optional[uuid.UUID] = None
    created_on: Optional[datetime] = None
    last_updated_by: Optional[uuid.UUID] = None
    last_updated_on: Optional[datetime] = None

    @classmethod
    def from_record(cls, record: dict) -> "ApiKey":
        """Build an ApiKey from a database row dict / asyncpg Record."""
        return cls(
            id=record["id"],
            api_key=record["api_key"],
            api_secret_hash=record["api_secret_hash"],
            is_active=record.get("is_active", True),
            created_by=record.get("created_by"),
            created_on=record.get("created_on"),
            last_updated_by=record.get("last_updated_by"),
            last_updated_on=record.get("last_updated_on"),
        )
