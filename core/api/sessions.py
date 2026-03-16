"""
core/api/sessions.py — Conversation session endpoints.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from core.pipelines.pipeline_builder import PipelineBuilder
from core.pipelines.pipeline_context import PipelineContext
from core.services import session_service, message_service, usage_service
from shared.config.config_cache import ConfigCache
from shared.utils.logging import get_logger

logger = get_logger("core.api.sessions")
router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


class MessageRequest(BaseModel):
    text: Optional[str] = None
    language: str = "en-IN"


class MessageResponse(BaseModel):
    session_id: str
    response_text: str
    response_audio_url: Optional[str] = None
    is_complete: bool = False
    latency_ms: dict[str, float]


@router.post("/{session_id}/message", response_model=MessageResponse)
async def process_message(
    session_id: uuid.UUID,
    request: Request,
    text: Optional[str] = Form(None),
    language: str = Form("en-IN"),
    audio: Optional[UploadFile] = File(None)
):
    """
    Process an incoming message (text or voice) through the pipeline.
    """
    business_id = uuid.UUID(request.state.business_id)
    schema_name = request.state.schema_name
    
    # 1. Fetch or load Client Config
    config_cache = ConfigCache.get_instance()
    client_config = config_cache.get_business_config(business_id)
    
    # 2. Prepare Pipeline Context
    audio_bytes = await audio.read() if audio else None
    
    context = PipelineContext(
        session_id=session_id,
        business_id=business_id,
        schema_name=schema_name,
        input_audio=audio_bytes,
        input_text=text,
        requested_language=language,
        client_config=client_config
    )

    # 3. Build and Run Pipeline
    # Channel is passed from request state (set in middleware)
    builder = PipelineBuilder()
    runner = builder.build(business_id, channel="web")
    
    try:
        await runner.run(context)
    except Exception as exc:
        logger.error(f"Pipeline failure: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Conversation pipeline failed")

    # 4. Persist Results (Audit)
    # User message
    user_msg_content = context.transcript or context.input_text or ""
    user_msg = await message_service.create_message(
        session_id=session_id,
        schema_name=schema_name,
        role="user",
        content=user_msg_content
    )

    # Assistant message
    assistant_msg = await message_service.create_message(
        session_id=session_id,
        schema_name=schema_name,
        role="assistant",
        content=context.final_response,
        is_unknown=context.is_unknown_query,
        rag_context=context.retrieved_chunks
    )

    # Record Usage
    await usage_service.record_usage(
        session_id=session_id,
        message_id=assistant_msg.id,
        schema_name=schema_name,
        stt_seconds=context.stt_seconds,
        llm_tokens=context.llm_tokens,
        tts_characters=context.tts_characters,
        latency_ms={k: int(v * 1000) for k, v in context.tracker.all().items()}
    )

    # 5. Handle Audio persistence (S3 upload would happen here in production)
    # For now, we return empty audio URL or mock path
    audio_url = None
    if context.final_audio:
        # mockup path
        audio_url = f"/api/v1/audio/{assistant_msg.id}.wav"

    return MessageResponse(
        session_id=str(session_id),
        response_text=context.final_response,
        response_audio_url=audio_url,
        is_complete=context.is_complete,
        latency_ms={k: v * 1000 for k, v in context.tracker.all().items()}
    )


@router.post("/", response_model=dict)
async def create_new_session(request: Request):
    """Start a new conversation session."""
    business_id = uuid.UUID(request.state.business_id)
    schema_name = request.state.schema_name
    user_id = request.state.user_identifier
    
    session = await session_service.create_session(
        schema_name=schema_name,
        channel="web",
        user_identifier=user_id
    )
    
    return {"session_id": str(session.id), "status": session.status}
