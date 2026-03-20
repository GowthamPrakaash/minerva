"""
shared/providers/tts/tts_elevenlabs.py — ElevenLabs TTS provider.

Implementation:
    Model: eleven_multilingual_v2
    API: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
"""

import os
import httpx

from shared.providers.base.tts_provider import TTSProvider
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger

logger = get_logger("shared.providers.tts.elevenlabs")


class TTSElevenLabs(TTSProvider):
    """ElevenLabs Text-to-Speech implementation (alternate)."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise EnvironmentError("ELEVENLABS_API_KEY not set")
        # Default voice ID (Rachel) - in production should be configurable
        self.voice_id = "21m00Tcm4TlpDqrrHC7E" 
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    async def text_to_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "rachel",
        pace: float = 1.0,
    ) -> bytes:
        """Synthesize speech using ElevenLabs Multilingual v2."""
        logger.debug(f"TTS ElevenLabs: Synthesizing {len(text)} chars")

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    json=payload
                )

            if response.status_code != 200:
                raise ProviderError(
                    self.provider_name,
                    f"ElevenLabs TTS failed: {response.status_code} - {response.text}"
                )

            logger.info(f"TTS ElevenLabs: Success. Generated {len(response.content)} bytes.")
            return response.content

        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, f"Network error: {exc}")
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(self.provider_name, f"Unexpected error: {exc}")
