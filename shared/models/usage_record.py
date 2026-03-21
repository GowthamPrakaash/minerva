"""
shared/models/usage_record.py — Usage tracking model.

Table: tenant_<slug>.usage_records

Fields:
    id, session_id, message_id, metrics, cost_estimate, latency_ms
"""

from __future__ import annotations

import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UsageRecord:
    """Represents a row in tenant_<slug>.usage_records."""

    id: uuid.UUID
    session_id: uuid.UUID           # FK → sessions.id
    message_id: uuid.UUID           # FK → messages.id
    metrics: dict = field(default_factory=dict)
    cost_estimate: float = 0.0
    latency_ms: Optional[dict[str, int]] = None  # Keyed by component name

    # Audit columns
    created_by: Optional[uuid.UUID] = None
    created_on: Optional[datetime] = None
    last_updated_by: Optional[uuid.UUID] = None
    last_updated_on: Optional[datetime] = None

    @classmethod
    def from_record(cls, record: dict) -> "UsageRecord":
        """Build a UsageRecord from a database row dict / asyncpg Record."""
        metrics_raw = record.get("metrics", "{}")
        metrics = json.loads(metrics_raw) if isinstance(metrics_raw, str) else (metrics_raw or {})
        
        latency_raw = record.get("latency_ms")
        latency = json.loads(latency_raw) if isinstance(latency_raw, str) else latency_raw

        return cls(
            id=record["id"],
            session_id=record["session_id"],
            message_id=record["message_id"],
            metrics=metrics,
            cost_estimate=record.get("cost_estimate", 0.0),
            latency_ms=latency,
            created_by=record.get("created_by"),
            created_on=record.get("created_on"),
            last_updated_by=record.get("last_updated_by"),
            last_updated_on=record.get("last_updated_on"),
        )
