"""
core/pipelines/components/stt_component.py — STT pipeline component.

Purpose:
    Converts input audio bytes to a text transcript.
    Critical component.
"""

from shared.providers.provider_resolver import ProviderResolver
from shared.exceptions.pipeline_exceptions import ProviderError
from shared.utils.logging import get_logger
from ..pipeline_context import PipelineContext

logger = get_logger("core.pipelines.components.stt")


class STTComponent:
    """Invokes the STT provider to transcribe audio."""

    @property
    def name(self) -> str:
        return "stt"

    @property
    def is_critical(self) -> bool:
        """STT is critical for voice input."""
        return True

    async def execute(self, context: PipelineContext) -> None:
        """
        Transcribe the input audio. Skipping if only text was provided.
        """
        if not context.input_audio:
            if context.input_text:
                context.transcript = context.input_text
                context.transcript_en = context.input_text  # Assume EN if text
                context.detected_language = "en-IN"
                logger.debug("STT: input_audio missing, using input_text as transcript")
                return
            else:
                raise ValueError("PipelineContext has no input (audio or text)")

        resolver = ProviderResolver.get_instance()
        provider = resolver.get_provider("stt", context.business_id)
        
        with context.tracker.measure("STT"):
            try:
                # 1. Try primary provider
                transcript, det_lang = await provider.transcribe(
                    context.input_audio,
                    context.requested_language
                )
            except ProviderError as exc:
                # 2. Try alternate provider on failure
                logger.warning(f"STT: primary provider '{provider.provider_name}' failed. Trying alternate.")
                alt_provider = resolver.get_alternate_provider("stt", provider.provider_name, context.business_id)
                
                if not alt_provider:
                    raise  # No alternate, original error bubbled up

                transcript, det_lang = await alt_provider.transcribe(
                    context.input_audio,
                    context.requested_language
                )

        if not transcript.strip():
            logger.info("STT: transcript is empty (silence or non-speech)")
        
        context.transcript = transcript
        context.detected_language = det_lang
        # Record usage
        context.stt_seconds = len(context.input_audio) / 32000.0  # Approx for 16kHz mono
        logger.info(f"STT: Transcribed '{transcript[:30]}...' (lang={det_lang})")
