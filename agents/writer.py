"""Writer agent contract and stub implementation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WriterRequest:
    branch_id: str
    prompt: str
    intensity: float


@dataclass(frozen=True)
class WriterResult:
    branch_id: str
    text: str
    prompt_version: str


def generate_branch_text(request: WriterRequest) -> WriterResult:
    """Return a deterministic placeholder response for early integration."""

    return WriterResult(
        branch_id=request.branch_id,
        text="",
        prompt_version="v0-stub",
    )
