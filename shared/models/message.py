"""
shared/models/message.py — Conversation message model.

Table: tenant_<slug>.messages

Fields:
    id, session_id (FK → sessions), role, content,
    audio_s3_path, is_unknown, rag_context (JSONB)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Message:
    """Represents a row in tenant_<slug>.messages."""

    id: uuid.UUID
    session_id: uuid.UUID           # FK → sessions.id
    role: str                       # 'user' | 'assistant' | 'system'
    content: str
    audio_s3_path: Optional[str] = None
    is_unknown: bool = False
    rag_context: Optional[list[dict[str, Any]]] = None

    # Audit columns
    created_by: Optional[uuid.UUID] = None
    created_on: Optional[datetime] = None
    last_updated_by: Optional[uuid.UUID] = None
    last_updated_on: Optional[datetime] = None

    @classmethod
    def from_record(cls, record: dict) -> "Message":
        """Build a Message from a database row dict / asyncpg Record."""
        return cls(
            id=record["id"],
            session_id=record["session_id"],
            role=record["role"],
            content=record["content"],
            audio_s3_path=record.get("audio_s3_path"),
            is_unknown=record.get("is_unknown", False),
            rag_context=record.get("rag_context"),
            created_by=record.get("created_by"),
            created_on=record.get("created_on"),
            last_updated_by=record.get("last_updated_by"),
            last_updated_on=record.get("last_updated_on"),
        )
