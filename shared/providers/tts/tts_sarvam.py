"""
shared/providers/tts/tts_sarvam.py — Sarvam AI TTS provider.

Implementation:
    Model: bulbul:v2
    API: POST https://api.sarvam.ai/text-to-speech
"""

import os
import base64
import struct
import httpx
from typing import Optional

from shared.providers.base.tts_provider import TTSProvider
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger

logger = get_logger("shared.providers.tts.sarvam")


class TTSSarvam(TTSProvider):
    """Sarvam AI Text-to-Speech implementation."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("SARVAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("SARVAM_API_KEY not set")
        self.url = "https://api.sarvam.ai/text-to-speech"

    @property
    def provider_name(self) -> str:
        return "sarvam"

    async def text_to_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "anushka",
        pace: float = 1.0,
    ) -> bytes:
        """
        Synthesize speech using Sarvam Bulbul v2.
        Handles base64 decoding and WAV header fix for concatenated chunks.
        """
        logger.debug(f"TTS Sarvam: Synthesizing {len(text)} chars (speaker={speaker}, pace={pace})")

        # Fallback for unknown language - POC uses en-IN
        if not language_code or language_code.lower() == "unknown":
            language_code = "en-IN"

        payload = {
            "text": text,
            "target_language_code": language_code,
            "speaker": speaker,
            "model": "bulbul:v2",
            "pace": pace,
            "response_format": "base64"
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    json=payload
                )

            if response.status_code != 200:
                raise ProviderError(
                    self.provider_name,
                    f"Sarvam TTS failed: {response.status_code} - {response.text}"
                )

            result = response.json()
            audios = result.get("audios", [])
            
            if not audios:
                raise ProviderError(self.provider_name, "Sarvam TTS returned no audio data")

            # Join all audio portions and fix WAV header
            full_audio = bytearray()
            for i, b64 in enumerate(audios):
                chunk = base64.b64decode(b64)
                if i == 0:
                    full_audio.extend(chunk)
                else:
                    # Skip the 44-byte WAV header for subsequent chunks
                    if len(chunk) > 44:
                        full_audio.extend(chunk[44:])
            
            # Update the Master WAV header with correct sizes
            if len(full_audio) > 44:
                # Offset 4 (file size - 8)
                full_audio[4:8] = struct.pack("<I", len(full_audio) - 8)
                # Offset 40 (data size)
                full_audio[40:44] = struct.pack("<I", len(full_audio) - 44)

            logger.info(f"TTS Sarvam: Success. Generated {len(full_audio)} bytes of audio.")
            return bytes(full_audio)

        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, f"Network error: {exc}")
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(self.provider_name, f"Unexpected error: {exc}")
