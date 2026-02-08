"""Artist agent contract and stub implementation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtistRequest:
    branch_id: str
    scene_plan: str
    seed: int


@dataclass(frozen=True)
class ArtistResult:
    branch_id: str
    image_count: int
    model_id: str


def generate_manga_panels(request: ArtistRequest) -> ArtistResult:
    """Return placeholder metadata for early orchestration wiring."""

    return ArtistResult(
        branch_id=request.branch_id,
        image_count=0,
        model_id="stub-model",
    )
