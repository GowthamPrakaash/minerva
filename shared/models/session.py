"""
shared/models/session.py — Conversation session model.

Table: tenant_<slug>.sessions

Fields:
    id, business_id, channel, user_identifier, language, status,
    conversation_summary, audio_s3_path, goal_state_json,
    last_activity, ended_at
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Session:
    """Represents a row in tenant_<slug>.sessions."""

    id: uuid.UUID
    # business_id: uuid.UUID          # REMOVED: Redundant as schema is per-business
    channel: str                    # 'web' | 'whatsapp' | 'phone'
    user_identifier: str            # end-user identifier from client system
    language: Optional[str] = None  # detected language code (e.g. 'en-IN')
    status: str = "active"          # 'active' | 'ended' | 'abandoned'
    conversation_summary: Optional[str] = None
    audio_s3_path: Optional[str] = None
    goal_state_json: Optional[dict[str, Any]] = field(default=None)
    last_activity: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Audit columns
    created_by: Optional[uuid.UUID] = None
    created_on: Optional[datetime] = None
    last_updated_by: Optional[uuid.UUID] = None
    last_updated_on: Optional[datetime] = None

    @classmethod
    def from_record(cls, record: dict) -> "Session":
        """Build a Session from a database row dict / asyncpg Record."""
        return cls(
            id=record["id"],
            channel=record["channel"],
            user_identifier=record["user_identifier"],
            language=record.get("language"),
            status=record.get("status", "active"),
            conversation_summary=record.get("conversation_summary"),
            audio_s3_path=record.get("audio_s3_path"),
            goal_state_json=record.get("goal_state_json"),
            last_activity=record.get("last_activity"),
            ended_at=record.get("ended_at"),
            created_by=record.get("created_by"),
            created_on=record.get("created_on"),
            last_updated_by=record.get("last_updated_by"),
            last_updated_on=record.get("last_updated_on"),
        )
