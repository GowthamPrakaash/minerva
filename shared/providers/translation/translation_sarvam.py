"""
shared/providers/translation/translation_sarvam.py — Sarvam AI Translation provider.

Implementation:
    Model: mayura:v1
    API: POST https://api.sarvam.ai/translate
"""

import os
import httpx

from shared.providers.base.translation_provider import TranslationProvider
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger

logger = get_logger("shared.providers.translation.sarvam")


class TranslationSarvam(TranslationProvider):
    """Sarvam AI Translation implementation."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("SARVAM_API_KEY")
        if not self.api_key:
            raise EnvironmentError("SARVAM_API_KEY not set")
        self.url = "https://api.sarvam.ai/translate"

    @property
    def provider_name(self) -> str:
        return "sarvam"

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate text using Sarvam Mayura v1."""
        logger.debug(f"Translate Sarvam: {source_language} -> {target_language}")

        payload = {
            "input": text,
            "source_language_code": source_language,
            "target_language_code": target_language,
            "speaker_gender": "Female",
            "mode": "formal",
            "model": "mayura:v1"
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
                    f"Sarvam Translation failed: {response.status_code} - {response.text}"
                )

            result = response.json()
            translated_text = result.get("translated_text", "").strip()
            
            logger.info(f"Translate Sarvam: Success. Text length: {len(translated_text)}")
            return translated_text

        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, f"Network error: {exc}")
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(self.provider_name, f"Unexpected error: {exc}")
