"""
shared/providers/base/stt_provider.py — STT provider interface.

Purpose:
    Abstract base class that all Speech-to-Text providers must implement.

Interface:
    class STTProvider(ABC):
        def transcribe(self, audio_bytes: bytes, language_code: str) -> tuple[str, str]
            Returns: (transcript, detected_language_code)
"""

from abc import ABC, abstractmethod


class STTProvider(ABC):
    """Abstract base class for all Speech-to-Text provider implementations."""

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language_code: str = "unknown",
    ) -> tuple[str, str]:
        """
        Convert raw audio bytes to a transcript.

        Args:
            audio_bytes:   Raw WAV audio data.
            language_code: BCP-47 language hint (e.g. 'en-IN'). Use 'unknown'
                           for auto-detection.

        Returns:
            Tuple of (transcript, detected_language_code).
            transcript is an empty string if nothing was spoken.

        Raises:
            ProviderError: If the API call fails.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'sarvam', 'deepgram')."""
        ...
