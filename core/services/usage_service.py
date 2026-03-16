"""
core/services/usage_service.py — Usage tracking service.
"""

import uuid
from typing import Optional
from core.repositories.message_repository import MessageRepository

async def record_usage(
    session_id: uuid.UUID,
    message_id: uuid.UUID,
    schema_name: str,
    stt_seconds: float = 0.0,
    llm_tokens: int = 0,
    tts_characters: int = 0,
    latency_ms: Optional[dict[str, float]] = None,
) -> None:
    # Logic remains here as it's business logic, but DB call is abstracted
    stt_cost = stt_seconds * 0.0001
    llm_cost = llm_tokens * 0.00001
    tts_cost = tts_characters * 0.000005
    cost_estimate = stt_cost + llm_cost + tts_cost

    metrics = {
        "stt_seconds": stt_seconds,
        "llm_tokens": llm_tokens,
        "tts_characters": tts_characters,
        "cost_estimate": cost_estimate,
        "latency_ms": latency_ms
    }
    
    repo = MessageRepository(schema_name)
    await repo.record_usage(session_id, message_id, metrics)
