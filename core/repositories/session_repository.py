"""
core/repositories/session_repository.py — Data access for Sessions.
"""

import uuid
from datetime import datetime
from typing import Optional
from shared.db.connection import get_connection
from shared.models.session import Session

class SessionRepository:
    """Encapsulates SQL logic for Sessions."""

    def __init__(self, schema_name: str):
        self.schema_name = schema_name

    async def create(self, channel: str, user_id: str) -> Session:
        query = """
        INSERT INTO sessions (id, channel, user_identifier, status)
        VALUES ($1, $2, $3, $4) RETURNING *
        """
        async with get_connection(self.schema_name) as conn:
            record = await conn.fetchrow(query, uuid.uuid4(), channel, user_id, "active")
            return Session.from_record(record)

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        async with get_connection(self.schema_name) as conn:
            record = await conn.fetchrow("SELECT * FROM sessions WHERE id = $1", session_id)
            return Session.from_record(record) if record else None

    async def update_summary(self, session_id: uuid.UUID, summary: str) -> None:
        async with get_connection(self.schema_name) as conn:
            await conn.execute("UPDATE sessions SET conversation_summary = $1 WHERE id = $2", summary, session_id)

    async def end(self, session_id: uuid.UUID) -> None:
        async with get_connection(self.schema_name) as conn:
            await conn.execute("UPDATE sessions SET status = 'ended', ended_at = $1 WHERE id = $2", datetime.now(), session_id)
