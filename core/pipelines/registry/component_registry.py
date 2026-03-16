"""
core/pipelines/registry/component_registry.py — Component map.

Purpose:
    Registry that maps string identifiers to component class implementations.
    Used by PipelineBuilder to instantiate pipelines.
"""

from ..components.stt_component import STTComponent
from ..components.translation_component import TranslationInComponent, TranslationOutComponent
from ..components.memory_component import MemoryComponent
from ..components.rag_component import RAGComponent
from ..components.goal_steering_component import GoalSteeringComponent
from ..components.llm_component import LLMComponent
from ..components.tts_component import TTSComponent

COMPONENT_REGISTRY = {
    "stt":            STTComponent,
    "translation_in": TranslationInComponent,
    "memory":         MemoryComponent,
    "rag":            RAGComponent,
    "goal_steering": GoalSteeringComponent,
    "llm":            LLMComponent,
    "translation_out": TranslationOutComponent,
    "tts":            TTSComponent,
}
