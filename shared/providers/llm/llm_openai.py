"""
shared/providers/llm/llm_openai.py — OpenAI LLM provider.

Implementation:
    Model: gpt-4o-mini (default)
    API: POST https://api.openai.com/v1/chat/completions
"""

import os
import httpx

from shared.providers.base.llm_provider import LLMProvider
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger

logger = get_logger("shared.providers.llm.openai")


class LLMOpenAI(LLMProvider):
    """OpenAI LLM implementation (used as alternate/fallback)."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("OPENAI_API_KEY not set")
        self.url = "https://api.openai.com/v1/chat/completions"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """Generate a response using OpenAI Chat API."""
        logger.debug(f"LLM OpenAI: Prompt length={len(user_prompt)}")

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
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
                    f"OpenAI LLM failed: {response.status_code} - {response.text}"
                )

            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            
            logger.info("LLM OpenAI: Success.")
            return answer

        except (httpx.RequestError, KeyError, IndexError) as exc:
            raise ProviderError(self.provider_name, f"LLM error: {exc}")
        except Exception as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError(self.provider_name, f"Unexpected error: {exc}")
