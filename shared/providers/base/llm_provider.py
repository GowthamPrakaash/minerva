"""
shared/providers/base/llm_provider.py — LLM provider interface.

Purpose:
    Abstract base class that all LLM providers must implement.

Interface:
    class LLMProvider(ABC):
        def chat_completion(self, system_prompt: str, user_prompt: str,
                          temperature: float, max_tokens: int) -> str
            Returns: generated text response
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for all LLM provider implementations."""

    @abstractmethod
    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate a text response from the LLM.

        Args:
            system_prompt: The system instruction / persona.
            user_prompt:   The user query with injected context.
            temperature:   Sampling temperature (0.0 for deterministic).
            max_tokens:    Maximum tokens in the response.

        Returns:
            The model's text response, stripped of leading/trailing whitespace.

        Raises:
            ProviderError: If the API call fails.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'sarvam', 'openai')."""
        ...
