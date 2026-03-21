"""
shared/providers/base/translation_provider.py — Translation provider interface.

Purpose:
    Abstract base class that all Translation providers must implement.

Interface:
    class TranslationProvider(ABC):
        def translate(self, text: str, source_lang: str, target_lang: str) -> str
            Returns: translated text
"""

from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    """Abstract base class for all Translation provider implementations."""

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        Translate text from source language to target language.

        Args:
            text:            The text to translate.
            source_language: BCP-47 source language code (e.g. 'hi-IN').
            target_language: BCP-47 target language code (e.g. 'en-IN').

        Returns:
            Translated text string.

        Raises:
            ProviderError: If the API call fails.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'sarvam')."""
        ...
