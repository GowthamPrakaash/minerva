"""
core/repositories/message_repository.py — Data access for Messages and Usage records.
"""

import uuid
import json
from typing import Optional, Any
from shared.db.connection import get_connection
from shared.models.message import Message

class MessageRepository:
    """Encapsulates SQL logic for conversation history and usage analytics."""

    def __init__(self, schema_name: str):
        self.schema_name = schema_name

    async def create(
        self, 
        session_id: uuid.UUID, 
        role: str, 
        content: str, 
        is_unknown: bool = False,
        rag_context: list = None
    ) -> Message:
        query = """
        INSERT INTO messages (session_id, role, content, is_unknown, rag_context)
        VALUES ($1, $2, $3, $4, $5) RETURNING *
        """
        async with get_connection(self.schema_name) as conn:
            record = await conn.fetchrow(
                query, session_id, role, content, is_unknown,
                json.dumps(rag_context) if rag_context else None
            )
            return Message.from_record(record)

    async def get_history(self, session_id: uuid.UUID, limit: int = 10) -> list[Message]:
        async with get_connection(self.schema_name) as conn:
            rows = await conn.fetch(
                "SELECT * FROM messages WHERE session_id = $1 ORDER BY created_on DESC LIMIT $2",
                session_id, limit
            )
            # Reverse to get chronological order
            return [Message.from_record(r) for r in reversed(rows)]

    async def record_usage(self, session_id: uuid.UUID, message_id: uuid.UUID, metrics: dict) -> None:
        query = """
        INSERT INTO usage_records (session_id, message_id, stt_seconds, llm_tokens, tts_characters, cost_estimate, latency_ms)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        async with get_connection(self.schema_name) as conn:
            await conn.execute(
                query, session_id, message_id,
                metrics.get("stt_seconds", 0),
                metrics.get("llm_tokens", 0),
                metrics.get("tts_characters", 0),
                metrics.get("cost_estimate", 0.0),
                json.dumps(metrics.get("latency_ms")) if metrics.get("latency_ms") else None
            )
