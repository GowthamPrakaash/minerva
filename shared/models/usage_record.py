"""
shared/models/usage_record.py — Usage tracking model.

Table: tenant_<slug>.usage_records

Fields:
    id, session_id, message_id, stt_seconds, llm_tokens,
    tts_characters, cost_estimate
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UsageRecord:
    """Represents a row in tenant_<slug>.usage_records."""

    id: uuid.UUID
    session_id: uuid.UUID           # FK → sessions.id
    message_id: uuid.UUID           # FK → messages.id
    stt_seconds: int = 0
    llm_tokens: int = 0
    tts_characters: int = 0
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
        return cls(
            id=record["id"],
            session_id=record["session_id"],
            message_id=record["message_id"],
            stt_seconds=record.get("stt_seconds", 0),
            llm_tokens=record.get("llm_tokens", 0),
            tts_characters=record.get("tts_characters", 0),
            cost_estimate=record.get("cost_estimate", 0.0),
            latency_ms=record.get("latency_ms"),
            created_by=record.get("created_by"),
            created_on=record.get("created_on"),
            last_updated_by=record.get("last_updated_by"),
            last_updated_on=record.get("last_updated_on"),
        )
