"""
shared/models/config.py — Per-tenant configuration model.

Table: tenant_<slug>.configs

Fields:
    id, config_key, config_value (JSONB), description
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Config:
    """Represents a row in tenant_<slug>.configs."""

    id: uuid.UUID
    config_key: str
    config_value: Any               # JSONB — can be dict, list, str, int, etc.
    description: Optional[str] = None

    # Audit columns
    created_by: Optional[uuid.UUID] = None
    created_on: Optional[datetime] = None
    last_updated_by: Optional[uuid.UUID] = None
    last_updated_on: Optional[datetime] = None

    @classmethod
    def from_record(cls, record: dict) -> "Config":
        """Build a Config from a database row dict / asyncpg Record."""
        return cls(
            id=record["id"],
            config_key=record["config_key"],
            config_value=record["config_value"],
            description=record.get("description"),
            created_by=record.get("created_by"),
            created_on=record.get("created_on"),
            last_updated_by=record.get("last_updated_by"),
            last_updated_on=record.get("last_updated_on"),
        )
