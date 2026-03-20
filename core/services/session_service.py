"""
core/services/session_service.py — Session management service.
"""

from __future__ import annotations
import uuid
from typing import Optional
from core.repositories.session_repository import SessionRepository
from shared.models.session import Session
from shared.utils.logging import get_logger

logger = get_logger("core.services.session_service")


async def create_session(
    schema_name: str,
    channel: str,
    user_identifier: str,
    created_by: Optional[uuid.UUID] = None
) -> Session:
    repo = SessionRepository(schema_name)
    session = await repo.create(channel, user_identifier)
    logger.info(f"SessionService: Created session {session.id}")
    return session


async def get_session(session_id: uuid.UUID, schema_name: str) -> Optional[Session]:
    repo = SessionRepository(schema_name)
    return await repo.get_by_id(session_id)


async def end_session(session_id: uuid.UUID, schema_name: str) -> None:
    repo = SessionRepository(schema_name)
    await repo.end(session_id)
    logger.info(f"SessionService: Ended session {session_id}")
