"""Writer agent interface backed by the text-generation engine."""

from __future__ import annotations

from core.retrieval_engine import HierarchicalMemoryModel, RetrievalIndex
from core.text_generation_engine import (
    PromptRegistry,
    VoiceCard,
    WriterEngine,
    WriterRequest,
    WriterResult,
)

_DEFAULT_WRITER_ENGINE = WriterEngine(prompt_registry=PromptRegistry())


def generate_branch_text(
    request: WriterRequest,
    *,
    retrieval_index: RetrievalIndex | None = None,
    memory_model: HierarchicalMemoryModel | None = None,
    writer_engine: WriterEngine | None = None,
) -> WriterResult:
    """Generate branch text through the configured writer engine."""

    engine = writer_engine or _DEFAULT_WRITER_ENGINE
    return engine.generate(
        request,
        retrieval_index=retrieval_index,
        memory_model=memory_model,
    )


__all__ = [
    "VoiceCard",
    "WriterEngine",
    "WriterRequest",
    "WriterResult",
    "generate_branch_text",
]
