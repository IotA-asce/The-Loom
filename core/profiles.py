"""Profile primitives for tone and maturity tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToneProfile:
    """Lightweight profile used during foundation phase."""

    tone_label: str
    maturity_score: float
    confidence: float

    def in_bounds(self) -> bool:
        return 0.0 <= self.maturity_score <= 1.0 and 0.0 <= self.confidence <= 1.0
