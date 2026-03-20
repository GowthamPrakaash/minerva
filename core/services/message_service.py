"""
core/services/message_service.py — Message persistence service.
"""

from __future__ import annotations
import uuid
from typing import Optional, Any
from core.repositories.message_repository import MessageRepository
from shared.models.message import Message

async def create_message(
    session_id: uuid.UUID,
    schema_name: str,
    role: str,
    content: str,
    audio_s3_path: Optional[str] = None,
    is_unknown: bool = False,
    rag_context: Optional[list[dict[str, Any]]] = None,
    created_by: Optional[uuid.UUID] = None
) -> Message:
    repo = MessageRepository(schema_name)
    return await repo.create(
        session_id=session_id,
        role=role,
        content=content,
        is_unknown=is_unknown,
        rag_context=rag_context
    )


async def get_messages(session_id: uuid.UUID, schema_name: str, limit: int = 10) -> list[Message]:
    repo = MessageRepository(schema_name)
    return await repo.get_history(session_id, limit)
