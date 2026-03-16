"""
shared/providers/base/tts_provider.py — TTS provider interface.

Purpose:
    Abstract base class that all Text-to-Speech providers must implement.

Interface:
    class TTSProvider(ABC):
        def text_to_speech(self, text: str, language_code: str,
                         speaker: str, pace: float) -> bytes
            Returns: WAV audio bytes
"""

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Abstract base class for all Text-to-Speech provider implementations."""

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        speaker: str = "anushka",
        pace: float = 1.0,
    ) -> bytes:
        """
        Convert text to WAV audio bytes.

        Args:
            text:          The text to synthesise.
            language_code: BCP-47 language code for the voice output.
            speaker:       Speaker voice name (provider-specific).
            pace:          Speech speed multiplier (0.5–2.0).

        Returns:
            WAV audio bytes ready for playback or streaming.

        Raises:
            ProviderError: If the API call fails.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'sarvam', 'elevenlabs')."""
        ...
