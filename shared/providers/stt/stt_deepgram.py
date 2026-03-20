"""
shared/providers/stt/stt_deepgram.py — Deepgram STT provider.

Implementation:
    Model: nova-2
    API: POST https://api.deepgram.com/v1/listen
"""

import os
import httpx
from typing import tuple

from shared.providers.base.stt_provider import STTProvider
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger

logger = get_logger("shared.providers.stt.deepgram")


class STTDeepgram(STTProvider):
    """Deepgram Speech-to-Text implementation (alternate)."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("DEEPGRAM_API_KEY not set")
        self.url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"

    @property
    def provider_name(self) -> str:
        return "deepgram"

    async def transcribe(
        self,
        audio_bytes: bytes,
        language_code: str = "unknown",
    ) -> tuple[str, str]:
        """Transcribe audio using Deepgram Nova-2."""
        logger.debug(f"STT Deepgram: Transcribing {len(audio_bytes)} bytes")

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }
        
        # Deepgram uses 'detect_language=true' for auto
        url = self.url
        if language_code == "unknown":
            url += "&detect_language=true"
        else:
            url += f"&language={language_code}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    content=audio_bytes
                )
                
            if response.status_code != 200:
                raise ProviderError(
                    self.provider_name,
                    f"Deepgram STT failed: {response.status_code} - {response.text}"
                )

            result = response.json()
            channels = result.get("results", {}).get("channels", [])
            if not channels:
                return "", "unknown"
                
            transcript = channels[0].get("alternatives", [{}])[0].get("transcript", "").strip()
            detected_lang = result.get("metadata", {}).get("detected_language", "unknown")
            
            logger.info(f"STT Deepgram: Success. Transcript='{transcript[:50]}...'")
            return transcript, detected_lang

        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, f"Network error: {exc}")
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(self.provider_name, f"Unexpected error: {exc}")
