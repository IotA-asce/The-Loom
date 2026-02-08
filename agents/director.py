"""Director agent helpers for coordinating writer and artist runs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationPlan:
    branch_id: str
    include_text: bool
    include_images: bool
    version_id: str


def create_generation_plan(branch_id: str) -> GenerationPlan:
    """Create a minimal generation plan for a branch."""

    return GenerationPlan(
        branch_id=branch_id,
        include_text=True,
        include_images=True,
        version_id="v0",
    )
