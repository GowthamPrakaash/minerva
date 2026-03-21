"""
shared/providers/stt/stt_sarvam.py — Sarvam AI STT provider.

Implementation:
    Model: saaras:v3
    API: POST https://api.sarvam.ai/speech-to-text
"""

import os
import httpx
from typing import tuple

from shared.providers.base.stt_provider import STTProvider
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger

logger = get_logger("shared.providers.stt.sarvam")


class STTSarvam(STTProvider):
    """Sarvam AI Speech-to-Text implementation."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("SARVAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("SARVAM_API_KEY not set")
        self.url = "https://api.sarvam.ai/speech-to-text"

    @property
    def provider_name(self) -> str:
        return "sarvam"

    async def transcribe(
        self,
        audio_bytes: bytes,
        language_code: str = "unknown",
    ) -> tuple[str, str]:
        """
        Transcribe audio using Sarvam Saaras v3.
        Note: language_code 'unknown' triggers auto-detection.
        """
        logger.debug(f"STT Sarvam: Transcribing {len(audio_bytes)} bytes (lang={language_code})")

        # Prepare multipart form data
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav")
        }
        data = {
            "model": "saaras:v3",
            "language_code": language_code if language_code != "unknown" else ""
        }
        headers = {"api-subscription-key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    data=data,
                    files=files
                )
                
            if response.status_code != 200:
                raise ProviderError(
                    self.provider_name,
                    f"Sarvam STT failed: {response.status_code} - {response.text}"
                )

            result = response.json()
            transcript = result.get("transcript", "").strip()
            detected_lang = result.get("language_code", "unknown")
            
            logger.info(f"STT Sarvam: Success. Transcript='{transcript[:50]}...', DetectedLang='{detected_lang}'")
            return transcript, detected_lang

        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, f"Network error: {exc}")
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(self.provider_name, f"Unexpected error: {exc}")
